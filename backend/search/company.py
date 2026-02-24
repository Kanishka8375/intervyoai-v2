"""
Company Research Module
Web search integration for company research during interviews
"""

import os
import json
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, field

import aiohttp
from loguru import logger


@dataclass
class CompanyInfo:
    name: str = ""
    industry: str = ""
    description: str = ""
    headquarters: str = ""
    founded: str = ""
    size: str = ""
    recent_news: List[Dict] = field(default_factory=list)
    interview_tips: List[str] = field(default_factory=list)


COMPANY_DATABASE = {
    "google": {
        "industry": "Technology / Internet",
        "description": "A multinational technology company specializing in Internet-related services and products.",
        "headquarters": "Mountain View, California",
        "founded": "1998",
        "size": "180,000+ employees",
        "values": ["Innovation", "User focus", "Transparency", "Growth mindset"],
    },
    "microsoft": {
        "industry": "Technology / Software",
        "description": "A global technology corporation that develops, manufactures, licenses, supports, and sells computer software.",
        "headquarters": "Redmond, Washington",
        "founded": "1975",
        "size": "220,000+ employees",
        "values": [
            "Diversity & Inclusion",
            "Growth Mindset",
            "Innovation",
            "Customer Obsession",
        ],
    },
    "amazon": {
        "industry": "E-commerce / Technology",
        "description": "An American multinational technology company focusing on e-commerce, cloud computing, and AI.",
        "headquarters": "Seattle, Washington",
        "founded": "1994",
        "size": "1.6+ million employees",
        "values": [
            "Customer Obsession",
            "Invent and Simplify",
            "Are Right, A Lot",
            "Learn and Be Curious",
        ],
    },
    "apple": {
        "industry": "Technology / Consumer Electronics",
        "description": "A multinational technology company that designs, develops, and sells consumer electronics.",
        "headquarters": "Cupertino, California",
        "founded": "1976",
        "size": "160,000+ employees",
        "values": ["Innovation", "Simplicity", "Privacy", "Excellence"],
    },
    "meta": {
        "industry": "Technology / Social Media",
        "description": "A technology company focused on building products that help people connect and share.",
        "headquarters": "Menlo Park, California",
        "founded": "2004",
        "size": "80,000+ employees",
        "values": ["Move Fast", "Be Bold", "Focus on Impact", "Open Source"],
    },
    "netflix": {
        "industry": "Entertainment / Streaming",
        "description": "A streaming service offering movies, TV shows, and original content.",
        "headquarters": "Los Gatos, California",
        "founded": "1997",
        "size": "14,000+ employees",
        "values": [
            "Customer Satisfaction",
            "Innovation",
            "Freedom & Responsibility",
            "Inclusion",
        ],
    },
    "tesla": {
        "industry": "Automotive / Energy",
        "description": "An electric vehicle and clean energy company designing, manufacturing, and selling EVs.",
        "headquarters": "Austin, Texas",
        "founded": "2003",
        "size": "130,000+ employees",
        "values": ["Innovation", "Sustainability", "Excellence", "Hard Work"],
    },
    "salesforce": {
        "industry": "Technology / CRM",
        "description": "A cloud-based software company providing CRM solutions and enterprise applications.",
        "headquarters": "San Francisco, California",
        "founded": "1999",
        "size": "70,000+ employees",
        "values": ["Trust", "Customer Success", "Innovation", "Equality"],
    },
    "adobe": {
        "industry": "Technology / Software",
        "description": "A software company specializing in creative and multimedia software products.",
        "headquarters": "San Jose, California",
        "founded": "1982",
        "size": "26,000+ employees",
        "values": ["Genuine", "Exceptional", "Innovative", "Involved"],
    },
    "ibm": {
        "industry": "Technology / Consulting",
        "description": "A global technology and consulting company offering IT services and solutions.",
        "headquarters": "Armonk, New York",
        "founded": "1911",
        "size": "260,000+ employees",
        "values": ["Innovation", "Trust", "Responsibility", "Client Focus"],
    },
}


class CompanyResearcher:
    """Research company information for interview preparation"""

    def __init__(self):
        self._cache: Dict[str, CompanyInfo] = {}

    async def search_company(self, company_name: str) -> CompanyInfo:
        """Search for company information"""
        if company_name in self._cache:
            return self._cache[company_name]

        company_key = company_name.lower().strip()

        if company_key in COMPANY_DATABASE:
            company_data = COMPANY_DATABASE[company_key]
            company_info = CompanyInfo(
                name=company_name.title(),
                industry=company_data["industry"],
                description=company_data["description"],
                headquarters=company_data["headquarters"],
                founded=company_data["founded"],
                size=company_data["size"],
                recent_news=await self._get_company_news(company_name),
                interview_tips=self._generate_interview_tips(
                    company_name, company_data
                ),
            )
        else:
            company_info = self._get_generic_info(company_name)
            try:
                news = await self._get_company_news(company_name)
                if news:
                    company_info.recent_news = news
            except:
                pass

        self._cache[company_name] = company_info
        return company_info

    async def _get_company_news(self, company_name: str) -> List[Dict]:
        """Get recent news about the company"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://news.google.com/rss/search?q={company_name}&hl=en-US&gl=US&ceid=US:en"
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        import re

                        text = await resp.text()
                        titles = re.findall(
                            r"<title><!\[CDATA\[(.*?)\]\]></title>", text
                        )
                        return [{"title": t, "snippet": ""} for t in titles[:5]]
        except Exception as e:
            logger.warning(f"News fetch failed: {e}")

        return []

    def _generate_interview_tips(self, company_name: str, data: Dict) -> List[str]:
        """Generate interview tips based on company data"""
        company = company_name.lower()
        tips = []

        tips.append(f"Research {company}'s mission and values")

        if "values" in data:
            tips.append(
                f"Align your answers with their values: {', '.join(data['values'][:2])}"
            )

        tips.extend(
            [
                "Prepare STAR method examples",
                "Research recent company news and products",
                "Prepare thoughtful questions for the interviewer",
                "Understand the role requirements thoroughly",
                "Be ready to discuss your relevant projects",
            ]
        )

        return tips

    def _get_generic_info(self, company_name: str) -> CompanyInfo:
        """Get generic company info for unknown companies"""
        return CompanyInfo(
            name=company_name.title(),
            description=f"Research {company_name} thoroughly before your interview. Understand their products, services, mission, and culture.",
            interview_tips=[
                f"Research {company_name}'s company culture and values",
                "Prepare STAR method behavioral examples",
                "Review the job description carefully",
                "Prepare questions for the interviewer",
                "Practice common interview questions",
                "Know your resume inside out",
            ],
        )


company_researcher = CompanyResearcher()
