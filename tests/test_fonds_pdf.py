import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.collectors import fonds_pdf
from app.collectors.run import seed_gerants
from app.db import Base
from app.models import AssetManager, Fund, SourceDocument


class ParsingTests(unittest.TestCase):
    def test_dernier_reporting_independance_pick_latest_by_date_prefix(self):
        html = """
        <a href="https://www.independance-am.com/wp-content/uploads/2025/12/251128-reporting-france-small-mid-x-eur-c2-fr.pdf">Nov</a>
        <a href="https://www.independance-am.com/wp-content/uploads/2026/07/260630-reporting-france-small-mid-x-eur-c2-fr-2-1.pdf">Juin</a>
        <a href="https://www.independance-am.com/wp-content/uploads/2026/01/251231-reporting-france-small-mid-x-eur-c2-fr-fr.pdf">Dec</a>
        """
        url, periode = fonds_pdf._dernier_reporting_independance(html)
        self.assertTrue(url.endswith("260630-reporting-france-small-mid-x-eur-c2-fr-2-1.pdf"))
        self.assertEqual(periode, "2026-06")

    def test_dernier_reporting_independance_absent(self):
        self.assertEqual(fonds_pdf._dernier_reporting_independance("<html></html>"), (None, None))

    def test_lien_document_amiral(self):
        html = (
            'foo docPermalink:"https:\\u002F\\u002Fcommandr-impress-amiral.nx.digital'
            '\\u002Fwebsite\\u002Fsextant_pme_FR0011171412_monthly_fr.pdf",url:bc'
        )
        url = fonds_pdf._lien_document_amiral(html)
        self.assertEqual(
            url, "https://commandr-impress-amiral.nx.digital/website/sextant_pme_FR0011171412_monthly_fr.pdf")

    def test_lien_document_amiral_absent(self):
        self.assertIsNone(fonds_pdf._lien_document_amiral("<html></html>"))

    def test_liens_documents_comgest(self):
        html = """
        <span class="fund-key-document-type fund-documents__document__type">
          Monthly Report
        </span>
        <div class="fund-key-document-links fund-documents__document__links">
            <div class="fund-key-document-link">
              <a href="https://www.comgest.com/-/media/x/463b.pdf"
                 data-language="FR" data-documentTypeCode="MR" data-documentDate="2026-06-30"
                 id="fundDocument1">FR</a>
            </div>
        </div>
        </div>
        """
        liens = fonds_pdf._liens_documents_comgest(html)
        self.assertEqual(liens["Monthly Report"], ("https://www.comgest.com/-/media/x/463b.pdf", "2026-06-30"))

    def test_mois_recul(self):
        import datetime

        self.assertEqual(fonds_pdf._mois_recul(datetime.date(2026, 1, 15), 0), datetime.date(2026, 1, 1))
        self.assertEqual(fonds_pdf._mois_recul(datetime.date(2026, 1, 15), 1), datetime.date(2025, 12, 1))
        self.assertEqual(fonds_pdf._mois_recul(datetime.date(2026, 1, 15), 2), datetime.date(2025, 11, 1))


class ArchiverDedupTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        manager = AssetManager(slug="moneta", nom="Moneta AM", type="boutique")
        self.session.add(manager)
        self.session.flush()
        self.fund = Fund(manager_id=manager.id, slug="moneta-multi-caps", nom="Moneta Multi Caps")
        self.session.add(self.fund)
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_archiver_creates_document_for_new_content(self):
        candidat = {"type": "fiche", "url": "https://example.test/a.pdf", "periode": "2026-06", "contenu": b"v1"}
        ajoute = fonds_pdf._archiver(self.session, self.fund, candidat)
        self.session.commit()
        self.assertTrue(ajoute)
        docs = self.session.scalars(select(SourceDocument)).all()
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].statut_extraction, "en_attente")
        self.assertEqual(docs[0].contenu, b"v1")

    def test_archiver_skips_unchanged_content(self):
        candidat = {"type": "fiche", "url": "https://example.test/a.pdf", "periode": "2026-06", "contenu": b"identique"}
        fonds_pdf._archiver(self.session, self.fund, candidat)
        self.session.commit()
        ajoute = fonds_pdf._archiver(self.session, self.fund, {**candidat, "periode": "2026-07"})
        self.session.commit()
        self.assertFalse(ajoute)
        self.assertEqual(len(self.session.scalars(select(SourceDocument)).all()), 1)

    def test_archiver_adds_new_document_when_content_changes(self):
        fonds_pdf._archiver(self.session, self.fund, {"type": "fiche", "url": "u", "periode": "2026-06", "contenu": b"v1"})
        self.session.commit()
        ajoute = fonds_pdf._archiver(self.session, self.fund, {"type": "fiche", "url": "u", "periode": "2026-07", "contenu": b"v2"})
        self.session.commit()
        self.assertTrue(ajoute)
        self.assertEqual(len(self.session.scalars(select(SourceDocument)).all()), 2)


class CollectBoutiquesPdfTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        seed_gerants(self.session)

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    @patch("app.collectors.fonds_pdf._recipe_comgest", return_value=[])
    @patch("app.collectors.fonds_pdf._recipe_lfde", return_value=[])
    @patch("app.collectors.fonds_pdf._recipe_carmignac", return_value=[])
    @patch("app.collectors.fonds_pdf._recipe_amiral", return_value=[])
    @patch("app.collectors.fonds_pdf._recipe_independance", return_value=[])
    @patch("app.collectors.fonds_pdf._recipe_moneta")
    def test_collect_archives_a_new_document_per_fund(self, moneta, *_others):
        moneta.return_value = [
            {"type": "fiche", "url": "https://moneta.test/a.pdf", "periode": "2026-06", "contenu": b"xyz"}]
        report = fonds_pdf.collect_boutiques_pdf(self.session)
        self.assertTrue(report["moneta-multi-caps"]["ok"])
        self.assertEqual(report["moneta-multi-caps"]["documents_ajoutes"], 1)
        fund = self.session.scalars(select(Fund).where(Fund.slug == "moneta-multi-caps")).first()
        docs = self.session.scalars(select(SourceDocument).where(SourceDocument.fund_id == fund.id)).all()
        self.assertEqual(len(docs), 1)

    @patch("app.collectors.fonds_pdf._recipe_comgest", side_effect=RuntimeError("gate HTTP 403"))
    @patch("app.collectors.fonds_pdf._recipe_lfde", return_value=[])
    @patch("app.collectors.fonds_pdf._recipe_carmignac", return_value=[])
    @patch("app.collectors.fonds_pdf._recipe_amiral", return_value=[])
    @patch("app.collectors.fonds_pdf._recipe_independance", return_value=[])
    @patch("app.collectors.fonds_pdf._recipe_moneta", return_value=[])
    def test_one_maison_failure_does_not_block_others(self, *_mocks):
        report = fonds_pdf.collect_boutiques_pdf(self.session)
        self.assertFalse(report["comgest-growth-europe"]["ok"])
        self.assertTrue(report["moneta-multi-caps"]["ok"])


if __name__ == "__main__":
    unittest.main()
