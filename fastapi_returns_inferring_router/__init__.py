from functools import wraps
from types import UnionType
from typing import (TYPE_CHECKING, Any, Callable, Union, get_args, get_origin, get_type_hints)

from fastapi import APIRouter
from fastapi.datastructures import DefaultPlaceholder
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from returns.result import Result, Success, Failure
from semantic_version import Version
import fastapi


class ReturnsInferringRouter(APIRouter):
    def __init__(
        self,
        *args,
        get_status_code: Callable[[Any], int] | None=None,
        merge_with_existing_responses: bool=True,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._get_status_code = get_status_code
        self._merge_with_existing_responses = merge_with_existing_responses

    if not TYPE_CHECKING:  # pragma: no branch

        def add_api_route(
            self, path: str, endpoint: Callable[..., Any], **kwargs: Any
        ) -> None:
            new_endpoint = endpoint

            return_type = get_type_hints(endpoint).get("return")

            if get_origin(return_type) is Result:
                @wraps(endpoint)
                def new_endpoint(*args, **kwargs):
                    ret = endpoint(*args, **kwargs)
                    match ret:
                        case Success(value):
                            return value
                        case Failure(value):
                            return JSONResponse(
                                status_code=self._get_status_code(value),
                                content=jsonable_encoder(value),
                            )

                suc_type, fail_type = get_args(return_type)

                # pydantic maps None to something openapi doesn't recognize
                if suc_type is None:
                    suc_type = Any
                kwargs["response_model"] = suc_type

                if (
                    kwargs.get("responses") is None or
                    self._merge_with_existing_responses
                ):
                    if get_origin(fail_type) in {Union, UnionType}:
                        fail_models = get_args(fail_type)
                    else:
                        fail_models = (fail_type,)
                    responses = kwargs.get("responses") or dict()
                    # codes can be e.g. "default" or "4xx" so we'll normalize
                    # the ones we can/{have to}
                    for k, v in list(responses.items()):
                        if isinstance(k, str) and k.isdecimal(k):
                            del responses[k]
                            responses[int(k)] = v
                    assert self._get_status_code is not None
                    for fail_model in fail_models:
                        code = self._get_status_code(fail_model)
                        # same pydantic issue as above
                        if fail_model is None:
                            fail_model = Any
                        if code in responses:
                            try:
                                responses[code]["model"] = Union[
                                    responses[code]["model"],
                                    fail_model,
                                ]
                            except KeyError:
                                raise ValueError(
                                    "fastapi_returns_inferring_router: "
                                    "Can't merge with response missing a "
                                    f"\"model\" key (for status code {code})"
                                )
                        else:
                            responses[code] = {"model": fail_model}
                    kwargs["responses"] = responses

            elif Version(fastapi.__version__) < Version("0.89.0"):
                # same pydantic issue as above
                if return_type is None:
                    return_type = Any
                if kwargs.get("response_model") is None:
                    kwargs["response_model"] = return_type


            return super().add_api_route(path, new_endpoint, **kwargs)

