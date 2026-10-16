"""Migração de junção (merge) entre dois ramos de migrações.

Duas migrações nasceram ao mesmo tempo a partir da 0004, em branches diferentes:

- ``0005_product_min_quantity_cashmovement`` (ramo da API: estoque mínimo e caixa)
- ``0005_remove_product_quantity_product_brand`` -> ``0006`` (ramo das telas: lotes)

Sem esta junção o Django recusa ``migrate`` com
"Conflicting migrations detected; multiple leaf nodes". Ela não altera o banco:
apenas declara que os dois ramos convergem aqui. É o mesmo arquivo que
``manage.py makemigrations --merge`` geraria.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("mercado", "0005_product_min_quantity_cashmovement"),
        ("mercado", "0006_alter_productbatch_batch_number_and_more"),
    ]

    operations = []
