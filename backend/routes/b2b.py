"""
InFinea — B2B Dashboard routes.
Company management, analytics, and employee features.
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
import uuid

from database import db
from auth import get_current_user
from models import CompanyCreate, InviteEmployee

router = APIRouter(prefix="/api")


@router.post("/b2b/company")
async def create_company(
    company_data: CompanyCreate,
    user: dict = Depends(get_current_user),
):
    """Create a B2B company account"""
    existing = await db.companies.find_one(
        {"admin_user_id": user["user_id"]}, {"_id": 0}
    )

    if existing:
        raise HTTPException(status_code=400, detail="You already have a company")

    company_id = f"company_{uuid.uuid4().hex[:12]}"
    company_doc = {
        "company_id": company_id,
        "name": company_data.name,
        "domain": company_data.domain,
        "admin_user_id": user["user_id"],
        "employees": [user["user_id"]],
        "employee_count": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.companies.insert_one(company_doc)

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"company_id": company_id, "is_company_admin": True}},
    )

    return {"company_id": company_id, "name": company_data.name}


@router.get("/b2b/company")
async def get_company(user: dict = Depends(get_current_user)):
    """Get company info for admin"""
    company_id = user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=404, detail="No company found")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return company


@router.get("/b2b/dashboard")
async def get_b2b_dashboard(user: dict = Depends(get_current_user)):
    """Get B2B analytics dashboard (anonymized QVT data)"""
    company_id = user.get("company_id")

    if not company_id or not user.get("is_company_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    employee_ids = company.get("employees", [])

    total_sessions = await db.user_sessions_history.count_documents(
        {"user_id": {"$in": employee_ids}, "completed": True}
    )

    total_time_pipeline = [
        {"$match": {"user_id": {"$in": employee_ids}, "completed": True}},
        {"$group": {"_id": None, "total": {"$sum": "$actual_duration"}}},
    ]
    total_time_result = await db.user_sessions_history.aggregate(
        total_time_pipeline
    ).to_list(1)
    total_time = total_time_result[0]["total"] if total_time_result else 0

    category_pipeline = [
        {"$match": {"user_id": {"$in": employee_ids}, "completed": True}},
        {
            "$group": {
                "_id": "$category",
                "count": {"$sum": 1},
                "time": {"$sum": "$actual_duration"},
            }
        },
    ]
    category_stats = await db.user_sessions_history.aggregate(
        category_pipeline
    ).to_list(10)

    four_weeks_ago = (datetime.now(timezone.utc) - timedelta(days=28)).isoformat()
    weekly_pipeline = [
        {
            "$match": {
                "user_id": {"$in": employee_ids},
                "completed": True,
                "completed_at": {"$gte": four_weeks_ago},
            }
        },
        {
            "$group": {
                "_id": {"$substr": ["$completed_at", 0, 10]},
                "sessions": {"$sum": 1},
                "time": {"$sum": "$actual_duration"},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    daily_activity = await db.user_sessions_history.aggregate(weekly_pipeline).to_list(
        28
    )

    one_week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    active_employees = await db.user_sessions_history.distinct(
        "user_id",
        {"user_id": {"$in": employee_ids}, "completed_at": {"$gte": one_week_ago}},
    )

    avg_time_per_employee = total_time / len(employee_ids) if employee_ids else 0
    avg_sessions_per_employee = (
        total_sessions / len(employee_ids) if employee_ids else 0
    )

    return {
        "company_name": company["name"],
        "employee_count": len(employee_ids),
        "active_employees_this_week": len(active_employees),
        "engagement_rate": round(
            len(active_employees) / len(employee_ids) * 100, 1
        )
        if employee_ids
        else 0,
        "total_sessions": total_sessions,
        "total_time_minutes": total_time,
        "avg_time_per_employee": round(avg_time_per_employee, 1),
        "avg_sessions_per_employee": round(avg_sessions_per_employee, 1),
        "category_distribution": {
            stat["_id"]: {"sessions": stat["count"], "time": stat["time"]}
            for stat in category_stats
        },
        "daily_activity": daily_activity,
        "qvt_score": min(
            100,
            round(
                len(active_employees) / len(employee_ids) * 100
                + (total_time / len(employee_ids) / 10)
                if employee_ids
                else 0,
                1,
            ),
        ),
    }


@router.post("/b2b/invite")
async def invite_employee(
    invite: InviteEmployee,
    user: dict = Depends(get_current_user),
):
    """Invite an employee to the company"""
    company_id = user.get("company_id")

    if not company_id or not user.get("is_company_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})

    email_domain = invite.email.split("@")[1]
    if email_domain != company["domain"]:
        raise HTTPException(
            status_code=400,
            detail=f"Email must be from {company['domain']} domain",
        )

    invite_id = f"invite_{uuid.uuid4().hex[:12]}"
    invite_doc = {
        "invite_id": invite_id,
        "company_id": company_id,
        "email": invite.email,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
    }

    await db.company_invites.insert_one(invite_doc)

    return {"invite_id": invite_id, "email": invite.email, "status": "pending"}


@router.get("/b2b/employees")
async def get_employees(user: dict = Depends(get_current_user)):
    """Get list of company employees (anonymized for privacy)"""
    company_id = user.get("company_id")

    if not company_id or not user.get("is_company_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})

    employee_ids = company.get("employees", [])

    employees = []
    for i, emp_id in enumerate(employee_ids):
        emp = await db.users.find_one({"user_id": emp_id}, {"_id": 0})
        if emp:
            sessions = await db.user_sessions_history.count_documents(
                {"user_id": emp_id, "completed": True}
            )
            employees.append(
                {
                    "employee_number": i + 1,
                    "name": emp.get("name", "Collaborateur"),
                    "total_time": emp.get("total_time_invested", 0),
                    "streak_days": emp.get("streak_days", 0),
                    "total_sessions": sessions,
                    "is_admin": emp_id == user["user_id"],
                }
            )

    return {"employees": employees, "total": len(employees)}
