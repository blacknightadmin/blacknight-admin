from wtforms import (
    Form,
    SelectField,
    IntegerField,
    DecimalField,
    ValidationError,
)
from wtforms.validators import InputRequired

from .queries import get_product_count


class CustomOrderItemForm(Form):
    order_id = SelectField(
        "Order",
        coerce=int,
        validators=[InputRequired()],
        render_kw={"class": "form-select"},
    )
    product_id = SelectField(
        "Product",
        coerce=int,
        validators=[InputRequired()],
        render_kw={"class": "form-select"},
    )
    count = IntegerField(
        "Count",
        validators=[InputRequired()],
        default=1,
        render_kw={"class": "form-control"},
    )
    price = DecimalField(
        "Price", validators=[InputRequired()], render_kw={"class": "form-control"}
    )

    def validate(self, extra_validators=None):
        validated = super().validate(extra_validators)
        product_count = get_product_count(self.product_id.data)
        if product_count < self.count.data:
            self.count.errors.append(
                f"There are only {product_count} items left in stock."
            )
            validated = False
        return validated


class ReturnOrderItemForm(Form):
    quantity_returned = IntegerField(
        "Quantity returned",
        validators=[InputRequired()],
        render_kw={"class": "form-control"},
    )

    def validate_quantity_returned(self, field):
        if field.data <= 0:
            raise ValidationError("Quantity must be 1 and above.")
