from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class AddressFieldsSchema(BaseModel):
    """A Mexican postal address split into fields. The backend joins them into a single text (`format_address`).

    Limits are chosen so the joined text always fits the 255-character `address` columns.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        str_strip_whitespace=True,
    )

    street: str = Field(..., min_length=1, max_length=70, description="Calle")
    exterior_number: str = Field(..., min_length=1, max_length=10, description="Número exterior")
    interior_number: str | None = Field(default=None, max_length=10, description="Número interior (opcional)")
    neighborhood: str = Field(..., min_length=1, max_length=50, description="Colonia")
    postal_code: str = Field(..., pattern=r"^\d{5}$", description="Código postal (5 dígitos)")
    municipality: str = Field(..., min_length=1, max_length=40, description="Municipio o alcaldía")
    state: str = Field(..., min_length=1, max_length=30, description="Estado")


def format_address(fields: AddressFieldsSchema) -> str:
    """Join the address fields into the single text stored in the legacy `address` columns.

    Example: ``Av. Reforma 100 Int. 4, Col. Centro, C.P. 06000, Cuauhtémoc, CDMX``.
    """
    number = f"{fields.street} {fields.exterior_number}"
    if fields.interior_number:
        number += f" Int. {fields.interior_number}"
    return ", ".join(
        [
            number,
            f"Col. {fields.neighborhood}",
            f"C.P. {fields.postal_code}",
            fields.municipality,
            fields.state,
        ],
    )
