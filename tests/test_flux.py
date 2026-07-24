import datetime
import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.collectors.run import seed_gerants, seed_instruments
from app.db import Base
from app.engine.flux import BITCOINS_EN_CIRCULATION, FENETRE_COURANT, bassin, courants
from app.models import AssetManager, Fund, FundSnapshot, Instrument, PriceDaily

DEBUT = datetime.date(2023, 1, 2)


class FluxTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        seed_instruments(self.session)
        seed_gerants(self.session)

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def cotes(self, code, closes, debut=DEBUT):
        instrument = self.session.scalar(select(Instrument).where(Instrument.code == code))
        self.session.add_all([
            PriceDaily(instrument_id=instrument.id, date=debut + datetime.timedelta(days=index), close=close)
            for index, close in enumerate(closes)
        ])
        self.session.commit()

    def depot_13f(self, slug_gerant, encours, date=datetime.date(2026, 3, 31)):
        manager = self.session.scalar(select(AssetManager).where(AssetManager.slug == slug_gerant))
        fund = self.session.scalar(select(Fund).where(Fund.manager_id == manager.id))
        self.session.add(FundSnapshot(fund_id=fund.id, date=date, encours=encours, nb_lignes_publiees=42))
        self.session.commit()

    # --- les lacs ---------------------------------------------------------------

    def test_stocks_sans_donnees_restent_des_ordres_de_grandeur_documentes(self):
        lacs = {lac["id"]: lac for lac in bassin(self.session)["lacs"]}
        self.assertEqual(lacs["actions"]["provenance"], "documente")
        self.assertTrue(lacs["actions"]["source"])
        self.assertNotIn("mesure", lacs["actions"])

    def test_le_stock_dor_est_valorise_au_cours_de_notre_base(self):
        self.cotes("or", [3000.0] * 5)
        lacs = {lac["id"]: lac for lac in bassin(self.session)["lacs"]}
        # 216 265 t × 32 150,7 onces × 3 000 $ ≈ 20,9 T$
        self.assertEqual(lacs["or"]["provenance"], "mesure")
        self.assertAlmostEqual(lacs["or"]["stock"], 20.86, places=1)
        self.assertEqual(lacs["or"]["mesure"]["date"], "2023-01-06")

    def test_le_stock_de_bitcoin_suit_le_cours_collecte(self):
        self.cotes("bitcoin", [100_000.0])
        lacs = {lac["id"]: lac for lac in bassin(self.session)["lacs"]}
        self.assertAlmostEqual(lacs["crypto"]["stock"], BITCOINS_EN_CIRCULATION * 100_000 / 1e12, places=2)

    def test_les_13f_eclairent_la_part_mesuree_des_collecteurs(self):
        self.depot_13f("blackrock", 3.2e12)
        self.depot_13f("vanguard", 2.8e12)
        self.depot_13f("berkshire", 0.3e12)
        lacs = {lac["id"]: lac for lac in bassin(self.session)["lacs"]}
        self.assertAlmostEqual(lacs["gerants"]["part_mesuree"]["stock"], 6.0, places=2)
        self.assertIn("BlackRock", lacs["gerants"]["part_mesuree"]["detail"])
        self.assertAlmostEqual(lacs["hedge_funds"]["part_mesuree"]["stock"], 0.3, places=2)
        # le total documenté reste l'estimation : la mesure ne le remplace pas
        self.assertEqual(lacs["gerants"]["stock"], 130)
        self.assertEqual(lacs["gerants"]["provenance"], "documente")

    def test_sans_depot_13f_aucune_part_mesuree_nest_affichee(self):
        lacs = {lac["id"]: lac for lac in bassin(self.session)["lacs"]}
        self.assertNotIn("part_mesuree", lacs["gerants"])

    # --- le courant -------------------------------------------------------------

    def test_pas_assez_dhistorique_ne_produit_aucun_courant(self):
        self.cotes("sp500", [100.0 + i for i in range(FENETRE_COURANT * 2)])
        self.assertEqual(courants(self.session), {})

    def test_une_mer_qui_monte_donne_un_souffle_positif(self):
        # une série qui grimpe régulièrement puis accélère sur le dernier mois
        closes = [100.0 + i * 0.1 for i in range(300)] + [130.0 + i for i in range(FENETRE_COURANT)]
        self.cotes("sp500", closes)
        lecture = courants(self.session)["actions"]
        self.assertGreater(lecture["variation"], 0)
        self.assertGreater(lecture["souffle"], 0.5)

    def test_un_taux_qui_baisse_fait_monter_les_obligations(self):
        # le taux 10 ans reflue sur le dernier mois : le prix des obligations monte
        closes = [4.0 + (i % 7) * 0.01 for i in range(300)] + [4.0 - i * 0.02 for i in range(FENETRE_COURANT)]
        self.cotes("us10y", closes)
        lecture = courants(self.session)["obligations"]
        self.assertGreater(lecture["variation"], 0)

    def test_le_souffle_reste_borne(self):
        closes = [100.0] * 300 + [100.0 * 3 ** i for i in range(FENETRE_COURANT)]
        self.cotes("bitcoin", closes)
        self.assertLessEqual(courants(self.session)["crypto"]["souffle"], 2.5)

    # --- le scénario du jour ----------------------------------------------------

    def test_le_scenario_du_jour_elargit_les_rivieres_dune_mer_qui_monte(self):
        closes = [100.0 + i * 0.1 for i in range(300)] + [130.0 + i * 2 for i in range(FENETRE_COURANT)]
        self.cotes("sp500", closes)
        scenario = bassin(self.session)["scenarios"]["aujourdhui"]
        self.assertEqual(scenario["nature"], "donnees")
        self.assertGreater(scenario["mult"]["gerants-actions"], 1)
        self.assertIn("Actions", scenario["note"])

    def test_une_chute_franche_inverse_la_riviere(self):
        closes = [100.0] * 300 + [100.0 * 0.9 ** i for i in range(FENETRE_COURANT)]
        self.cotes("bitcoin", closes)
        mult = bassin(self.session)["scenarios"]["aujourdhui"]["mult"]
        self.assertLess(mult["hedge_funds-crypto"], 0)

    def test_sans_donnees_le_scenario_du_jour_ne_ment_pas(self):
        scenario = bassin(self.session)["scenarios"]["aujourdhui"]
        self.assertEqual(scenario["mult"], {})
        self.assertIn("Pas encore de courant lisible", scenario["note"])

    def test_les_scenarios_pedagogiques_sont_etiquetes_comme_tels(self):
        scenarios = bassin(self.session)["scenarios"]
        self.assertEqual([cle for cle, s in scenarios.items() if s["nature"] == "pedagogique"],
                         ["calme", "qe", "riskoff"])

    # --- cohérence du graphe ----------------------------------------------------

    def test_chaque_riviere_relie_deux_lacs_existants(self):
        payload = bassin(self.session)
        ids = {lac["id"] for lac in payload["lacs"]}
        for riviere in payload["rivieres"]:
            self.assertIn(riviere["de"], ids)
            self.assertIn(riviere["vers"], ids)

    def test_les_multiplicateurs_ne_visent_que_des_rivieres_connues(self):
        payload = bassin(self.session)
        ids = {riviere["id"] for riviere in payload["rivieres"]}
        for scenario in payload["scenarios"].values():
            for cible in scenario["mult"]:
                self.assertIn(cible, ids)


if __name__ == "__main__":
    unittest.main()
