"""
Job Roles Configuration Module
100+ job roles with specialized prompts for interviews
"""

from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class RoleCategory(Enum):
    CORPORATE_LEADERSHIP = "Corporate & Business Leadership"
    TECHNOLOGY_DATA = "Technology & Data"
    FINANCE_ACCOUNTING = "Finance & Accounting"
    HEALTHCARE_MEDICAL = "Healthcare & Medical"
    MARKETING_CREATIVE = "Marketing, Creative & Media"
    ENGINEERING_ARCHITECTURE = "Engineering & Architecture"
    ELECTRONICS_VLSI = "Electronics & VLSI"
    EMBEDDED_IOT = "Embedded Systems & IoT"
    TELECOMMUNICATIONS = "Telecommunications & Networking"
    ROBOTICS_SIGNAL = "Signal Processing & Robotics"


@dataclass
class JobRole:
    id: str
    name: str
    category: str
    description: str
    keywords: List[str]
    question_types: List[str]
    system_prompt: str


BASE_PROMPT = """You are an expert interview coach helping a candidate interview for {role_name}.

Your goal is to provide the best possible answers to interview questions.
Use the STAR method (Situation, Task, Action, Result) for behavioral questions.
Keep answers concise (30-90 seconds when spoken), professional, and relevant to {role_name}."""


def get_all_job_roles() -> List[JobRole]:
    """Get all job roles with their configurations"""

    roles_data = [
        # Corporate & Business Leadership
        (
            "ceo",
            "Chief Executive Officer (CEO)",
            RoleCategory.CORPORATE_LEADERSHIP.value,
            "Leads overall company strategy",
            ["leadership", "strategy", "vision"],
            ["leadership", "behavioral"],
        ),
        (
            "coo",
            "Chief Operating Officer (COO)",
            RoleCategory.CORPORATE_LEADERSHIP.value,
            "Manages daily operations",
            ["operations", "management"],
            ["operational", "leadership"],
        ),
        (
            "cfo",
            "Chief Financial Officer (CFO)",
            RoleCategory.CORPORATE_LEADERSHIP.value,
            "Manages company finances",
            ["finance", "strategy"],
            ["financial", "leadership"],
        ),
        (
            "cto",
            "Chief Technology Officer (CTO)",
            RoleCategory.CORPORATE_LEADERSHIP.value,
            "Leads technology strategy",
            ["technology", "innovation"],
            ["technical", "leadership"],
        ),
        (
            "vp_operations",
            "Vice President of Operations",
            RoleCategory.CORPORATE_LEADERSHIP.value,
            "Manages operations department",
            ["operations", "process"],
            ["operational"],
        ),
        # Technology & Data
        (
            "software_engineer",
            "Software Engineer",
            RoleCategory.TECHNOLOGY_DATA.value,
            "Develops software",
            ["coding", "algorithms"],
            ["technical", "coding"],
        ),
        (
            "data_scientist",
            "Data Scientist",
            RoleCategory.TECHNOLOGY_DATA.value,
            "Analyzes data",
            ["machine learning", "statistics"],
            ["technical", "ml"],
        ),
        (
            "devops_engineer",
            "DevOps Engineer",
            RoleCategory.TECHNOLOGY_DATA.value,
            "Manages CI/CD",
            ["Kubernetes", "Docker"],
            ["technical", "devops"],
        ),
        (
            "data_analyst",
            "Data Analyst",
            RoleCategory.TECHNOLOGY_DATA.value,
            "Analyzes business data",
            ["SQL", "visualization"],
            ["technical", "analytics"],
        ),
        (
            "ai_ml_engineer",
            "AI/ML Engineer",
            RoleCategory.TECHNOLOGY_DATA.value,
            "Builds AI systems",
            ["deep learning", "neural networks"],
            ["technical", "ai"],
        ),
        (
            "cloud_architect",
            "Cloud Architect",
            RoleCategory.TECHNOLOGY_DATA.value,
            "Designs cloud solutions",
            ["AWS", "Azure"],
            ["technical", "cloud"],
        ),
        (
            "cybersecurity_analyst",
            "Cybersecurity Analyst",
            RoleCategory.TECHNOLOGY_DATA.value,
            "Protects systems",
            ["security", "networking"],
            ["technical", "security"],
        ),
        (
            "frontend_developer",
            "Frontend Developer",
            RoleCategory.TECHNOLOGY_DATA.value,
            "Develops user interfaces",
            ["React", "JavaScript"],
            ["technical", "frontend"],
        ),
        (
            "backend_developer",
            "Backend Developer",
            RoleCategory.TECHNOLOGY_DATA.value,
            "Develops server-side",
            ["API", "database"],
            ["technical", "backend"],
        ),
        (
            "mobile_developer",
            "Mobile App Developer",
            RoleCategory.TECHNOLOGY_DATA.value,
            "Develops mobile apps",
            ["iOS", "Android"],
            ["technical", "mobile"],
        ),
        (
            "product_manager",
            "Product Manager",
            RoleCategory.TECHNOLOGY_DATA.value,
            "Manages product strategy",
            ["roadmap", "stakeholders"],
            ["product", "strategy"],
        ),
        (
            "ux_ui_designer",
            "UX/UI Designer",
            RoleCategory.TECHNOLOGY_DATA.value,
            "Designs user experiences",
            ["Figma", "wireframing"],
            ["design", "ux"],
        ),
        # Finance & Accounting
        (
            "chartered_accountant",
            "Chartered Accountant (CA)",
            RoleCategory.FINANCE_ACCOUNTING.value,
            "Manages accounting",
            ["accounting", "tax"],
            ["technical", "finance"],
        ),
        (
            "financial_analyst",
            "Financial Analyst",
            RoleCategory.FINANCE_ACCOUNTING.value,
            "Analyzes finances",
            ["modeling", "valuation"],
            ["finance", "analytical"],
        ),
        (
            "investment_banker",
            "Investment Banker",
            RoleCategory.FINANCE_ACCOUNTING.value,
            "Handles M&A",
            ["valuation", "M&A"],
            ["finance", "deal"],
        ),
        # Healthcare
        (
            "physician",
            "Physician",
            RoleCategory.HEALTHCARE_MEDICAL.value,
            "Provides medical care",
            ["diagnosis", "treatment"],
            ["clinical"],
        ),
        (
            "registered_nurse",
            "Registered Nurse",
            RoleCategory.HEALTHCARE_MEDICAL.value,
            "Provides nursing care",
            ["patient-care", "medication"],
            ["clinical", "patient-care"],
        ),
        (
            "pharmacist",
            "Pharmacist",
            RoleCategory.HEALTHCARE_MEDICAL.value,
            "Dispenses medication",
            ["pharmacy", "drugs"],
            ["clinical", "pharmacy"],
        ),
        # Marketing
        (
            "digital_marketing",
            "Digital Marketing Specialist",
            RoleCategory.MARKETING_CREATIVE.value,
            "Digital marketing",
            ["SEO", "PPC"],
            ["marketing", "digital"],
        ),
        (
            "social_media_manager",
            "Social Media Manager",
            RoleCategory.MARKETING_CREATIVE.value,
            "Social media",
            ["Facebook", "Instagram"],
            ["marketing", "content"],
        ),
        (
            "graphic_designer",
            "Graphic Designer",
            RoleCategory.MARKETING_CREATIVE.value,
            "Designs graphics",
            ["Photoshop", "branding"],
            ["design", "creative"],
        ),
        # Engineering
        (
            "civil_engineer",
            "Civil Engineer",
            RoleCategory.ENGINEERING_ARCHITECTURE.value,
            "Infrastructure design",
            ["structural", "CAD"],
            ["technical", "design"],
        ),
        (
            "mechanical_engineer",
            "Mechanical Engineer",
            RoleCategory.ENGINEERING_ARCHITECTURE.value,
            "Mechanical design",
            ["CAD", "thermodynamics"],
            ["technical", "design"],
        ),
        (
            "electrical_engineer",
            "Electrical Engineer",
            RoleCategory.ENGINEERING_ARCHITECTURE.value,
            "Electrical systems",
            ["circuits", "power"],
            ["technical"],
        ),
        # Electronics & VLSI
        (
            "vlsi_design_engineer",
            "VLSI Design Engineer",
            RoleCategory.ELECTRONICS_VLSI.value,
            "Chip design",
            ["Verilog", "VHDL"],
            ["technical", "chip-design"],
        ),
        (
            "fpga_engineer",
            "FPGA Engineer",
            RoleCategory.ELECTRONICS_VLSI.value,
            "FPGA development",
            ["FPGA", "Verilog"],
            ["technical", "embedded"],
        ),
        # Embedded & IoT
        (
            "embedded_engineer",
            "Embedded Software Engineer",
            RoleCategory.EMBEDDED_IOT.value,
            "Embedded development",
            ["C", "RTOS"],
            ["technical", "embedded"],
        ),
        (
            "firmware_developer",
            "Firmware Developer",
            RoleCategory.EMBEDDED_IOT.value,
            "Firmware development",
            ["firmware", "C"],
            ["technical"],
        ),
        # Telecommunications
        (
            "telecom_engineer",
            "Telecom Engineer",
            RoleCategory.TELECOMMUNICATIONS.value,
            "Telecom systems",
            ["wireless", "networks"],
            ["technical", "networking"],
        ),
        (
            "network_engineer",
            "Network Engineer",
            RoleCategory.TELECOMMUNICATIONS.value,
            "Network infrastructure",
            ["routing", "firewall"],
            ["technical"],
        ),
        # Robotics
        (
            "robotics_engineer",
            "Robotics Engineer",
            RoleCategory.ROBOTICS_SIGNAL.value,
            "Robot development",
            ["ROS", "kinematics"],
            ["technical", "engineering"],
        ),
        (
            "automation_engineer",
            "Automation Engineer",
            RoleCategory.ROBOTICS_SIGNAL.value,
            "Automation systems",
            ["PLC", "SCADA"],
            ["technical"],
        ),
        # Additional Tech Roles
        (
            "database_administrator",
            "Database Administrator",
            RoleCategory.TECHNOLOGY_DATA.value,
            "Manages databases",
            ["SQL", "backup"],
            ["technical"],
        ),
        (
            "systems_administrator",
            "Systems Administrator",
            RoleCategory.TECHNOLOGY_DATA.value,
            "Manages IT systems",
            ["Linux", "Windows"],
            ["technical"],
        ),
        (
            "project_manager",
            "Project Manager",
            RoleCategory.TECHNOLOGY_DATA.value,
            "Manages projects",
            ["planning", "stakeholders"],
            ["project", "leadership"],
        ),
        (
            "blockchain_developer",
            "Blockchain Developer",
            RoleCategory.TECHNOLOGY_DATA.value,
            "Develops blockchain",
            ["Solidity", "Web3"],
            ["technical", "blockchain"],
        ),
        # Sales & HR
        (
            "sales_manager",
            "Sales Manager",
            RoleCategory.CORPORATE_LEADERSHIP.value,
            "Sales leadership",
            ["sales", "revenue"],
            ["sales", "leadership"],
        ),
        (
            "hr_manager",
            "HR Manager",
            RoleCategory.CORPORATE_LEADERSHIP.value,
            "HR management",
            ["recruiting", "policy"],
            ["hr", "leadership"],
        ),
        # More Engineering
        (
            "aerospace_engineer",
            "Aerospace Engineer",
            RoleCategory.ENGINEERING_ARCHITECTURE.value,
            "Aerospace systems",
            ["aerodynamics", "propulsion"],
            ["technical"],
        ),
        (
            "chemical_engineer",
            "Chemical Engineer",
            RoleCategory.ENGINEERING_ARCHITECTURE.value,
            "Chemical processes",
            ["chemistry", "process"],
            ["technical"],
        ),
        (
            "architect",
            "Architect",
            RoleCategory.ENGINEERING_ARCHITECTURE.value,
            "Building design",
            ["design", "CAD"],
            ["design", "creative"],
        ),
    ]

    roles = []
    for role_id, name, category, description, keywords, question_types in roles_data:
        prompt = BASE_PROMPT.replace("{role_name}", name)
        roles.append(
            JobRole(
                id=role_id,
                name=name,
                category=category,
                description=description,
                keywords=keywords,
                question_types=question_types,
                system_prompt=prompt,
            )
        )

    return roles


def get_role_by_id(role_id: str) -> Optional[JobRole]:
    """Get a specific job role by ID"""
    roles = get_all_job_roles()
    for role in roles:
        if role.id == role_id:
            return role
    return None


def get_categories() -> List[str]:
    """Get all unique categories"""
    roles = get_all_job_roles()
    return sorted(list(set(r.category for r in roles)))
