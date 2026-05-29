from pydantic import BaseModel, ConfigDict


class SchemeModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    def model_post_init(self, __context) -> None:
        # only run if extras exist
        extras = getattr(self, "__pydantic_extra__", None)

        if extras:
            print(
                f"[{__name__}] Unknown fields in {self.__class__.__name__}: {list(extras.items())}",
            )
