"""AppConfig za apps.media_pipeline — image + PDF utility (cross-cutting).

Story 2.3 (Epic 2) — utility app bez modela. Konzumiran od domain app-ova
(brands, products, blog) kroz template tagove i helper-e.
Jednosmerna zavisnost: media_pipeline NE SME uvoziti apps.products / apps.brands.

Story 2.4 (Epic 2) — DODATO: ready() hook wire-uje post_save signal za
ProductBrochure (auto-generation cover_thumbnail_image kroz pdf2image).
Sender se resolviše kasno kroz apps.get_model("products", "ProductBrochure")
da očuva Story 2.3 AC8 boundary rule (no `apps.products` import u media_pipeline).
"""

from django.apps import AppConfig
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _


class MediaPipelineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.media_pipeline"
    verbose_name = _("Media pipeline")

    def ready(self) -> None:
        """Wire post_save signal za ProductBrochure cover thumbnail generator.

        Mora biti import-ovan unutar ready() (NE module-level) jer:
        (a) apps.products još nije loaded pri Django startup-u kad se ovaj fajl
            importuje (INSTALLED_APPS resolve order). `ready()` je guaranteed
            pozvan posle svih AppConfig.import_models().
        (b) signals.py import-uje pdf_utils.py koji import-uje pdf2image — drugi
            testovi koji ne diraju signals ne treba da učitavaju pdf2image / poppler.
        (c) apps.get_model() je kasna resolucija — ne krši AST boundary check
            (string-based "products.ProductBrochure" NIJE statički import).

        dispatch_uid sprečava double-connect ako se ready() slučajno pozove
        dva puta (pytest-django edge case sa multiple app config reloads).
        """
        from django.apps import apps

        from apps.media_pipeline.signals import handle_brochure_post_save

        product_brochure_model = apps.get_model("products", "ProductBrochure")
        post_save.connect(
            handle_brochure_post_save,
            sender=product_brochure_model,
            dispatch_uid="apps.media_pipeline.signals.handle_brochure_post_save",
        )
