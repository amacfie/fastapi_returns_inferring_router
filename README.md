Combines InferringRouter from [fastapi-utils](https://fastapi-utils.davidmontague.xyz/user-guide/inferring-router/)
and Result from [returns](https://returns.readthedocs.io/en/latest/pages/result.html#api-reference)
so that both primary (200) and [additional](https://fastapi.tiangolo.com/advanced/additional-responses/)
response types can be inferred from the path operation type signature.

Install as user
```bash
pip install git+https://github.com/amacfie/fastapi_returns_inferring_router
```


Install as developer
```bash
pip install --editable .
```


# How to use

```python
from typing import Literal

from pydantic import BaseModel
from returns.result import Result, Success, Failure
import fastapi

from fastapi_returns_inferring_router import ReturnsInferringRouter


class ForbiddenBecauseOfUser(BaseModel):
    def status_code(*args):
        return 403

    msg: Literal["Forbidden because of user"] = "Forbidden because of user"


class ForbiddenBecauseOfKey(BaseModel):
    def status_code(*args):
        return 403

    msg: Literal["Forbidden because of key"] = "Forbidden because of key"


app = fastapi.FastAPI()

# one param is added to APIRouter, called get_status_code.
# pass a function that can take either a return type or return value and returns
# the HTTP status code you wish to use it for
r = ReturnsInferringRouter(get_status_code=lambda x: x.status_code())

# compatible with InferringRouter from fastapi-utils
@r.get("/foo/{bar}")
def foo(bar: str) -> str:
    return bar + "b"


# use the Returns library to write a function with a return type of Result.
# the success type becomes the 200 response type
# any failure types are also added as response types under the status code
# given by get_status_code.
# here we have two types with the same status code so the schema for 403 will
# be the union of the two types
@r.get("/baz/{bar}")
def baz(bar: str) -> Result[str, ForbiddenBecauseOfKey | ForbiddenBecauseOfUser]:
    if ...:
        return Failure(ForbiddenBecauseOfKey())
    elif ...:
        return Failure(ForbiddenBecauseOfUser())
    else:
        return Success(bar + "b")


app.include_router(r)
```

Generated schema (paste to <https://editor.swagger.io/> for nicer view):
```json
{
  "openapi": "3.0.2",
  "info": {
    "title": "FastAPI",
    "version": "0.1.0"
  },
  "paths": {
    "/foo/{bar}": {
      "get": {
        "summary": "Foo",
        "operationId": "foo_foo__bar__get",
        "parameters": [
          {
            "required": true,
            "schema": {
              "title": "Bar",
              "type": "string"
            },
            "name": "bar",
            "in": "path"
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "title": "Response Foo Foo  Bar  Get",
                  "type": "string"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/baz/{bar}": {
      "get": {
        "summary": "Baz",
        "operationId": "baz_baz__bar__get",
        "parameters": [
          {
            "required": true,
            "schema": {
              "title": "Bar",
              "type": "string"
            },
            "name": "bar",
            "in": "path"
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "title": "Response Baz Baz  Bar  Get",
                  "type": "string"
                }
              }
            }
          },
          "403": {
            "description": "Forbidden",
            "content": {
              "application/json": {
                "schema": {
                  "title": "Response 403 Baz Baz  Bar  Get",
                  "anyOf": [
                    {
                      "$ref": "#/components/schemas/ForbiddenBecauseOfKey"
                    },
                    {
                      "$ref": "#/components/schemas/ForbiddenBecauseOfUser"
                    }
                  ]
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "ForbiddenBecauseOfKey": {
        "title": "ForbiddenBecauseOfKey",
        "type": "object",
        "properties": {
          "msg": {
            "title": "Msg",
            "enum": [
              "Forbidden because of key"
            ],
            "type": "string",
            "default": "Forbidden because of key"
          }
        }
      },
      "ForbiddenBecauseOfUser": {
        "title": "ForbiddenBecauseOfUser",
        "type": "object",
        "properties": {
          "msg": {
            "title": "Msg",
            "enum": [
              "Forbidden because of user"
            ],
            "type": "string",
            "default": "Forbidden because of user"
          }
        }
      },
      "HTTPValidationError": {
        "title": "HTTPValidationError",
        "type": "object",
        "properties": {
          "detail": {
            "title": "Detail",
            "type": "array",
            "items": {
              "$ref": "#/components/schemas/ValidationError"
            }
          }
        }
      },
      "ValidationError": {
        "title": "ValidationError",
        "required": [
          "loc",
          "msg",
          "type"
        ],
        "type": "object",
        "properties": {
          "loc": {
            "title": "Location",
            "type": "array",
            "items": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "integer"
                }
              ]
            }
          },
          "msg": {
            "title": "Message",
            "type": "string"
          },
          "type": {
            "title": "Error Type",
            "type": "string"
          }
        }
      }
    }
  }
}
```
