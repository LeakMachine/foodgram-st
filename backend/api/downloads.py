from io import BytesIO
from django.http import HttpResponse
from django.db.models import Sum
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from recipes.models import Ingredient


def generate_shopping_list_txt(user):
    ingredients = Ingredient.objects.filter(
        used_in__recipe__shoppingcart__user=user
    ).values('title', 'unit').annotate(total=Sum('used_in__quantity'))
    lines = [
        f"{item['title']} ({item['unit']}) — {item['total']}"
        for item in ingredients
    ]
    content = "".join(lines)
    response = HttpResponse(content, content_type='text/plain')
    response[
        'Content-Disposition'
    ] = 'attachment; filename="shopping_list.txt"'
    return response


def generate_shopping_list_pdf(user):
    ingredients = Ingredient.objects.filter(
        used_in__recipe__shoppingcart__user=user
    ).values('title', 'unit').annotate(total=Sum('used_in__quantity'))

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    p.setFont("Helvetica", 12)
    p.drawString(50, y, "Список покупок:")
    y -= 25

    for item in ingredients:
        line = f"{item['title']} ({item['unit']}) — {item['total']}"
        p.drawString(50, y, line)
        y -= 20
        if y < 50:
            p.showPage()
            y = 750

    p.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response[
        'Content-Disposition'
    ] = 'attachment; filename="shopping_list.pdf"'
    return response
