from bs4 import BeautifulSoup
from backend.core.models import UIElement
import uuid

def parse_html(path: str):
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    elements = []

    form_elements = soup.find_all(["input", "button", "select"])

    for el in form_elements:
        el_id = str(uuid.uuid4())
        tag = el.name
        element_type = el.get("type", tag)
        name = el.get("name")
        html_id = el.get("id")
        text = el.text.strip() if el.text else None

        if html_id:
            selector = f"#{html_id}"
        elif name:
            selector = f'[name="{name}"]'
        else:
            selector = tag

        elements.append(
            UIElement(
                id=el_id,
                tag=tag,
                element_type=element_type,
                name=name,
                html_id=html_id,
                text=text,
                selector=selector
            )
        )

    return elements
