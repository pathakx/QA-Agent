from fastapi import APIRouter
from pydantic import BaseModel
from backend.services.testcase_service import generate_testcases
from backend.services.selenium_service import generate_selenium_script

router = APIRouter()

class TestCaseRequest(BaseModel):
    query: str

class ScriptRequest(BaseModel):
    testcase: dict

@router.post("/testcases")
def testcase_generation(req: TestCaseRequest):
    return generate_testcases(req.query)

@router.post("/selenium-script")
def create_script(req: ScriptRequest):
    script = generate_selenium_script(req.testcase)
    return {"script": script}
