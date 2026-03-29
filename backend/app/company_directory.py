from app.routers.sectors import SECTORS


def _label_from_slug(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.replace("-", " ").split())


def build_company_directory() -> list[dict[str, str]]:
    unique: dict[tuple[str, str], dict[str, str]] = {}
    for companies in SECTORS.values():
        for c in companies:
            source = c["source"]
            slug = c["slug"]
            key = (source, slug)
            if key not in unique:
                unique[key] = {
                    "source": source,
                    "slug": slug,
                    "label": _label_from_slug(slug),
                }
    return sorted(unique.values(), key=lambda item: (item["label"], item["source"]))


COMPANY_DIRECTORY = build_company_directory()
