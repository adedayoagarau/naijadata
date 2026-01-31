#!/usr/bin/env python3
"""
NIGERIAN STATE BUDGET DATABASE - 2025 & 2026
All 36 States + FCT

Last Updated: January 30, 2026
Sources: Official State Government Websites, News Reports

Status Key:
- SIGNED = Governor has signed into law
- PASSED = Assembly passed, awaiting signature
- PROPOSED = Presented to Assembly
- PENDING = Not yet presented
"""

# =============================================================================
# FEDERAL GOVERNMENT
# =============================================================================
FEDERAL = {
    "2025": {
        "total": "₦54.99 trillion",
        "status": "SIGNED",
        "name": "Budget of Restoration",
        "capital": "₦13.08 trillion deficit"
    },
    "2026": {
        "total": "₦58.18 trillion",
        "status": "PENDING PASSAGE",
        "name": "Budget of Consolidation, Renewed Resilience and Shared Prosperity",
        "capital": "₦26.08 trillion",
        "recurrent": "₦15.25 trillion",
        "debt_service": "₦14.3-15.5 trillion",
        "revenue_target": "₦34.33 trillion",
        "presented": "December 19, 2025"
    }
}

# =============================================================================
# ALL 36 STATES + FCT
# =============================================================================
STATES = {
    # =========================================================================
    # SOUTH WEST (6 States)
    # =========================================================================
    "lagos": {
        "name": "Lagos",
        "region": "South West",
        "portal": "https://lagosmepb.org/",
        "website": "https://lagosstate.gov.ng/",
        "2025": {
            "total": "₦3.366 trillion",
            "status": "SIGNED",
            "docs": {
                "appropriation_law": "https://lagosmepb.org/wp-content/uploads/LAGOS-STATE-2025-Appropriation-Law-1.pdf",
                "approved_ncoa": "https://lagosmepb.org/wp-content/uploads/Lagos-State-Y2025-Budget-NCOA-1.pdf",
                "citizens": "https://lagosmepb.org/wp-content/uploads/Y2025-Lagos-State-Citizens-Budget.pdf",
                "q1_report": "https://lagosmepb.org/wp-content/uploads/Y2025-Lagos-State-Budget-Implementation-Report-FY25.pdf"
            }
        },
        "2026": {
            "total": "₦4.445 trillion",
            "status": "SIGNED",
            "name": "Budget of Shared Prosperity",
            "capital": "₦2.338 trillion",
            "recurrent": "₦2.107 trillion",
            "increase": "32% from 2025"
        }
    },

    "ogun": {
        "name": "Ogun",
        "region": "South West",
        "portal": "https://ogunstate.gov.ng/budget/",
        "website": "https://ogunstate.gov.ng/",
        "2025": {
            "total": "₦1.054 trillion",
            "status": "SIGNED",
            "name": "Budget of Hope and Prosperity",
            "docs": {
                "approved": "https://api.ogunstate.gov.ng/archive/OGUNStateFY2025BudgetPublicationV4.pdf",
                "q1_report": "https://api.ogunstate.gov.ng/archive/OGUNSTATEQ12025BIR3-CBPRPublicationTemplateWORDDOCUMENT2FINALCHRIS27FEB.pdf"
            }
        },
        "2026": {
            "total": "₦1.669 trillion",
            "status": "SIGNED",
            "name": "Budget of Sustainable Legacy",
            "increase": "58% from 2025",
            "signed_date": "January 1, 2026"
        }
    },

    "oyo": {
        "name": "Oyo",
        "region": "South West",
        "portal": "https://budget.oyostate.gov.ng/",
        "website": "https://oyostate.gov.ng/",
        "2025": {
            "total": "₦678 billion",
            "status": "SIGNED",
            "docs": {
                "appropriation_law": "https://budget.oyostate.gov.ng/download/oyo-state-fy-2025-appropriation-law/",
                "citizens": "https://budget.oyostate.gov.ng/wp-content/uploads/2025/03/OYOSTATE-CITIZENS-BUDGET-2025.pdf",
                "q2_report": "https://budget.oyostate.gov.ng/wp-content/uploads/2025/07/OYO-STATE-BUDGET-PERFORMANCE-REPORT-FOR-YEAR-2025-SECOND-QUARTER.pdf"
            }
        },
        "2026": {
            "total": "₦892 billion",
            "status": "SIGNED",
            "education": "₦155.21 billion (17.4%)"
        }
    },

    "osun": {
        "name": "Osun",
        "region": "South West",
        "portal": "https://www.osunstate.gov.ng/",
        "website": "https://www.osunstate.gov.ng/",
        "2025": {
            "total": "₦427.75 billion",
            "status": "SIGNED",
            "docs": {
                "approved": "https://www.osunstate.gov.ng/wp-content/uploads/2025/01/2025-OSUN-STATE-APPROVED-BUDGET.pdf"
            }
        },
        "2026": {
            "total": "₦723.4 billion",
            "status": "SIGNED",
            "recurrent_revenue": "₦421.25 billion",
            "capital_receipts": "₦286.01 billion"
        }
    },

    "ondo": {
        "name": "Ondo",
        "region": "South West",
        "portal": "https://www.ondobudget.org/",
        "website": "https://ondostate.gov.ng/",
        "2025": {
            "total": "₦698.66 billion",
            "status": "SIGNED",
            "name": "Budget of Recovery",
            "capital": "₦433.62 billion (62%)",
            "recurrent": "₦265.04 billion (38%)",
            "docs": {
                "download_page": "https://www.ondobudget.org/download_budget.php"
            }
        },
        "2026": {
            "total": "₦524.41 billion",
            "status": "SIGNED",
            "capital": "₦303.58 billion (57.9%)",
            "education": "₦77.02 billion (15%)",
            "docs": {
                "download_page": "https://www.ondobudget.org/download_budget.php"
            }
        }
    },

    "ekiti": {
        "name": "Ekiti",
        "region": "South West",
        "portal": "https://www.ekitistate.gov.ng/finance-budget",
        "website": "https://www.ekitistate.gov.ng/",
        "2025": {
            "total": "₦375.79 billion",
            "status": "SIGNED",
            "docs": {
                "mtef": "https://ekitistate.gov.ng/wp-content/uploads/2025/2025-2027%20Multi-Year%20Budget%20Framework.pdf",
                "q1_report": "https://www.ekitistate.gov.ng/wp-content/uploads/2025/2025_Q1.pdf"
            }
        },
        "2026": {
            "total": "₦415.37 billion",
            "status": "SIGNED",
            "capital": "47%",
            "recurrent": "53%"
        }
    },

    # =========================================================================
    # SOUTH SOUTH (6 States)
    # =========================================================================
    "rivers": {
        "name": "Rivers",
        "region": "South South",
        "portal": "https://www.riversstate.gov.ng/",
        "website": "https://www.riversstate.gov.ng/",
        "2025": {
            "total": "₦1.48 trillion",
            "status": "SIGNED",
            "note": "Under special administration (Vice Admiral Ibok-Ete Ibas)",
            "docs": {
                "approved": "https://www.riversstate.gov.ng/wp-content/uploads/2025/01/RIVERS-State-FY-2025-Budget-Publication-1-1.pdf"
            }
        },
        "2026": {
            "total": "PENDING",
            "status": "NOT YET PRESENTED",
            "note": "Political situation - Governor Fubara has not yet presented 2026 budget"
        }
    },

    "akwa_ibom": {
        "name": "Akwa Ibom",
        "region": "South South",
        "portal": "https://www.aksbudgetoffice.ak.gov.ng/",
        "website": "https://akwaibomstate.gov.ng/",
        "2025": {
            "total": "₦955 billion",
            "status": "SIGNED",
            "docs": {
                "approved": "https://www.aksbudgetoffice.ak.gov.ng/budgets/E-Budget/2025/Akwa_Ibom_State_2025_Approved_Budget.pdf",
                "appropriation_law": "https://www.aksbudgetoffice.ak.gov.ng/budgets/Appropriation%20Laws2/2025/Appropriation_Law_2025.pdf"
            }
        },
        "2026": {
            "total": "₦1.584 trillion",
            "status": "SIGNED",
            "name": "People's Budget of Expansion and Growth",
            "capital": "₦1.168 trillion (73.7%)",
            "recurrent": "₦416.59 billion (26.3%)",
            "education": "₦31.6 billion (2.27% - lowest)"
        }
    },

    "delta": {
        "name": "Delta",
        "region": "South South",
        "portal": "https://deltastate.gov.ng/",
        "website": "https://deltastate.gov.ng/",
        "2025": {
            "total": "₦936 billion",
            "status": "SIGNED",
            "capital": "₦587.4 billion (62.75%)",
            "recurrent": "₦348.7 billion (37.25%)"
        },
        "2026": {
            "total": "₦1.729 trillion",
            "status": "SIGNED",
            "name": "Budget of Accelerating the MORE Agenda",
            "signed_date": "December 16, 2025",
            "docs": {
                "portal": "https://deltastate.gov.ng/"
            }
        }
    },

    "edo": {
        "name": "Edo",
        "region": "South South",
        "portal": "https://edostate.gov.ng/",
        "website": "https://edostate.gov.ng/",
        "2025": {
            "total": "₦675.22 billion",
            "status": "SIGNED",
            "name": "Budget of Renewed Hope for A Rising Edo",
            "docs": {
                "proposed": "https://edostate.gov.ng/wp-content/uploads/2025/01/FY-2025-Proposed-Budget_Print.pdf"
            }
        },
        "2026": {
            "total": "₦939.85 billion",
            "status": "SIGNED",
            "capital": "₦637 billion (67.8%)"
        }
    },

    "bayelsa": {
        "name": "Bayelsa",
        "region": "South South",
        "portal": "https://bayelsastate.gov.ng/",
        "website": "https://bayelsastate.gov.ng/",
        "2025": {
            "total": "₦582.7 billion",
            "status": "SIGNED",
            "docs": {
                "approved": "https://www.mof.by.gov.ng/uploads/BAYELSA%20State%20FY%202025%20Budget%20Publication%20pdf.pdf",
                "budget_uploads": "https://www.mof.by.gov.ng/budget_uploads"
            }
        },
        "2026": {
            "total": "₦1.01 trillion",
            "status": "SIGNED",
            "name": "Budget of Assured Prosperity II",
            "signed_date": "December 23, 2025",
            "docs": {
                "budget_uploads": "https://www.mof.by.gov.ng/budget_uploads"
            }
        }
    },

    "cross_river": {
        "name": "Cross River",
        "region": "South South",
        "portal": "https://www.crossriverstate.gov.ng/",
        "website": "https://www.crossriverstate.gov.ng/",
        "2025": {
            "total": "₦384.54 billion",
            "status": "SIGNED",
            "docs": {
                "mtef": "https://www.crossriverstate.gov.ng/download/2025-2027%20CRS%20FSP%20and%20MTEF.pdf"
            }
        },
        "2026": {
            "total": "₦961 billion",
            "status": "SIGNED",
            "social_services": "₦163 billion",
            "increase": "₦180 billion added by Assembly"
        }
    },

    # =========================================================================
    # SOUTH EAST (5 States)
    # =========================================================================
    "abia": {
        "name": "Abia",
        "region": "South East",
        "portal": "https://abiastate.gov.ng/document-category/budgets/",
        "website": "https://abiastate.gov.ng/",
        "2025": {
            "total": "₦750.2 billion",
            "status": "SIGNED",
            "capital": "₦611.7 billion (82%)",
            "recurrent": "₦138.5 billion (18%)",
            "docs": {
                "citizens": "https://abiastate.gov.ng/wp-content/uploads/2025/03/ABIA-STATE-2025-CITIZENS-BUDGET.pdf"
            }
        },
        "2026": {
            "total": "₦1.016 trillion",
            "status": "SIGNED",
            "education": "₦203.2 billion (20%)"
        }
    },

    "anambra": {
        "name": "Anambra",
        "region": "South East",
        "portal": "https://mbep.anambrastate.gov.ng/",
        "website": "https://anambrastate.gov.ng/",
        "2025": {
            "total": "₦607 billion",
            "status": "SIGNED",
            "name": "Changing Gears 2.0",
            "docs": {
                "mtef": "https://anambrastate.gov.ng/wp-content/uploads/Approved-MTEF_-2024-2026.pdf",
                "documents_page": "https://anambrastate.gov.ng/documents/"
            }
        },
        "2026": {
            "total": "₦766.37 billion",
            "status": "SIGNED",
            "note": "Increased from ₦757 billion proposal",
            "education": "30%+ (leads nation)",
            "docs": {
                "documents_page": "https://anambrastate.gov.ng/documents/"
            }
        }
    },

    "enugu": {
        "name": "Enugu",
        "region": "South East",
        "portal": "https://mbp.en.gov.ng/",
        "website": "https://en.gov.ng/",
        "2025": {
            "total": "₦971 billion",
            "status": "SIGNED",
            "name": "Budget of Exponential Growth and Inclusive Prosperity",
            "capital": "₦837.9 billion (86%)",
            "recurrent": "₦133.1 billion (14%)",
            "docs": {
                "documents_page": "https://mbp.en.gov.ng/bdocuments/"
            }
        },
        "2026": {
            "total": "₦1.62 trillion",
            "status": "SIGNED",
            "capital": "₦1.296 trillion (80%)",
            "recurrent": "₦321.3 billion (20%)",
            "education": "30%+ (leads nation)",
            "signed_date": "December 24, 2025"
        }
    },

    "ebonyi": {
        "name": "Ebonyi",
        "region": "South East",
        "portal": "https://ebonyistate.gov.ng/ministry/budgets-and-planning/",
        "website": "https://ebonyistate.gov.ng/",
        "2025": {
            "total": "₦383.6 billion",
            "status": "SIGNED",
            "docs": {
                "approved": "https://ebonyistate.gov.ng/storage/documents/min-1-ebsg-2025-approved-budgetpdf-1738259476.pdf"
            }
        },
        "2026": {
            "total": "₦884.87 billion",
            "status": "SIGNED",
            "capital": "₦749.49 billion (84.7% - highest in nation)",
            "social_services": "₦247.97 billion"
        }
    },

    "imo": {
        "name": "Imo",
        "region": "South East",
        "portal": "https://imostate.gov.ng/",
        "website": "https://imostate.gov.ng/",
        "2025": {
            "total": "₦807 billion",
            "status": "SIGNED",
            "note": "Increased from ₦756 billion proposed",
            "docs": {
                "approved": "https://s3.eu-west-2.amazonaws.com/openstates.ng.storage/documents/dataset_IMSG_2024_Budget_ver-Approved.pdf",
                "budget_portal": "https://imostate.gov.ng/IMSG/Services/EGov/Budget"
            }
        },
        "2026": {
            "total": "₦1.4 trillion",
            "status": "SIGNED",
            "name": "Budget of Economic Breakthrough",
            "education": "₦60.62 billion (4.24% - second lowest)",
            "signed_date": "December 24, 2025",
            "docs": {
                "budget_portal": "https://imostate.gov.ng/IMSG/Services/EGov/Budget"
            }
        }
    },

    # =========================================================================
    # NORTH WEST (7 States)
    # =========================================================================
    "kano": {
        "name": "Kano",
        "region": "North West",
        "portal": "https://budget.kn.gov.ng/",
        "website": "https://kanostate.gov.ng/",
        "2025": {
            "total": "₦719.76 billion",
            "status": "SIGNED",
            "docs": {
                "approved": "https://budget.kn.gov.ng/wp-content/uploads/2025/02/KANO-State-FY-2025-Budget-Updated-Copy.pdf"
            }
        },
        "2026": {
            "total": "₦1.477 trillion",
            "status": "SIGNED",
            "capital": "₦934.6 billion (63.3%)",
            "education": "₦405.3 billion (30% - 2nd highest)"
        }
    },

    "kaduna": {
        "name": "Kaduna",
        "region": "North West",
        "portal": "https://pbc.kdsg.gov.ng/",
        "website": "https://kdsg.gov.ng/",
        "2025": {
            "total": "₦790 billion",
            "status": "SIGNED",
            "docs": {
                "approved": "https://s3.eu-west-2.amazonaws.com/openstates.ng.storage/documents/dataset_Kaduna-State-Government-2023-Approved-Budget.pdf",
                "budget_documents": "http://pbc.kdsg.gov.ng/?page_id=669"
            }
        },
        "2026": {
            "total": "₦985.9 billion",
            "status": "SIGNED",
            "capital": "₦698.9 billion (70.9%)",
            "education": "₦246.25 billion (25%)",
            "docs": {
                "budget_documents": "http://pbc.kdsg.gov.ng/?page_id=669"
            }
        }
    },

    "katsina": {
        "name": "Katsina",
        "region": "North West",
        "portal": "https://katsinastate.gov.ng/",
        "website": "https://katsinastate.gov.ng/",
        "2025": {
            "total": "₦548.7 billion",
            "status": "SIGNED"
        },
        "2026": {
            "total": "₦897 billion",
            "status": "SIGNED",
            "education": "₦156.3 billion (17.4%)",
            "docs": {
                "appropriation_law": "https://katsinastate.gov.ng/ova_doc/katsina-state-government-2026-approved-appropriation-law/"
            }
        }
    },

    "sokoto": {
        "name": "Sokoto",
        "region": "North West",
        "portal": "https://sokotostate.gov.ng/",
        "website": "https://sokotostate.gov.ng/",
        "2025": {
            "total": "₦526.88 billion",
            "status": "SIGNED",
            "docs": {
                "approved": "https://sokotostate.gov.ng/wp-content/uploads/2025/01/Approved-budget-2025.pdf",
                "q1_report": "https://sokotostate.gov.ng/wp-content/uploads/2025/04/Sokoto-State-2025-Q1-BIR3-C-BPR-Publication-Template-WL-APRIL-2025-2CN_updated-CR.pdf"
            }
        },
        "2026": {
            "total": "₦758.7 billion",
            "status": "SIGNED",
            "name": "Budget of Socio-Economic Expansion",
            "capital": "72%",
            "recurrent": "28%",
            "health": "₦122.73 billion (16%)",
            "education": "₦115.95 billion",
            "signed_date": "January 30, 2026"
        }
    },

    "zamfara": {
        "name": "Zamfara",
        "region": "North West",
        "portal": "https://zamfarastate.gov.ng/",
        "website": "https://zamfarastate.gov.ng/",
        "2025": {
            "total": "₦420 billion",
            "status": "SIGNED"
        },
        "2026": {
            "total": "TBD",
            "status": "SIGNED",
            "docs": {
                "approved": "https://zamfara.gov.ng/wp-content/uploads/2026/01/ZAMFARA-STATE-2026-APPROVED-BUDGET-ESTIMATES_compressed-1.pdf"
            }
        }
    },

    "kebbi": {
        "name": "Kebbi",
        "region": "North West",
        "portal": "https://kebbistate.gov.ng/",
        "website": "https://kebbistate.gov.ng/",
        "2025": {
            "total": "₦293.9 billion",
            "status": "SIGNED"
        },
        "2026": {
            "total": "₦642.93 billion",
            "status": "SIGNED",
            "education": "₦105 billion (16%)",
            "docs": {
                "approved": "https://www.kebbistate.gov.ng/sites/default/files/2026%20APPROVED%20BUDGET_Final.pdf"
            }
        }
    },

    "jigawa": {
        "name": "Jigawa",
        "region": "North West",
        "portal": "https://jigawastate.gov.ng/",
        "website": "https://jigawastate.gov.ng/",
        "2025": {
            "total": "₦372.9 billion",
            "status": "SIGNED"
        },
        "2026": {
            "total": "₦901.84 billion",
            "status": "SIGNED",
            "education": "₦234.48 billion (26%)",
            "docs": {
                "approved": "https://jsbepd.org/images/jsbepd_pics/2026/Budget%202026/Jigawa%20State%20Government_%20Fiscal%20Year%202026%20Approved%20Estimates_.pdf"
            }
        }
    },

    # =========================================================================
    # NORTH EAST (6 States)
    # =========================================================================
    "adamawa": {
        "name": "Adamawa",
        "region": "North East",
        "portal": "https://www.budgetoffice.ad.gov.ng/",
        "website": "https://adamawastate.gov.ng/",
        "2025": {
            "total": "₦374.9 billion",
            "status": "SIGNED"
        },
        "2026": {
            "total": "TBD",
            "status": "SIGNED",
            "docs": {
                "approved": "https://adamawastate.gov.ng/ova_doc/adamawa-state-fy-2026-approved-budget/"
            }
        }
    },

    "bauchi": {
        "name": "Bauchi",
        "region": "North East",
        "portal": "https://bauchistate.gov.ng/",
        "website": "https://bauchistate.gov.ng/",
        "2025": {
            "total": "₦397.5 billion",
            "status": "SIGNED",
            "docs": {
                "approved": "https://www.bauchistate.gov.ng/wp-content/uploads/2025/01/Bauchi-State-2025-Approved-Budget.pdf",
                "financial_reports": "https://www.bauchistate.gov.ng/financial-reports-2/"
            }
        },
        "2026": {
            "total": "₦878 billion",
            "status": "SIGNED",
            "education": "₦131.71 billion (15%)",
            "docs": {
                "financial_reports": "https://www.bauchistate.gov.ng/financial-reports-2/"
            }
        }
    },

    "borno": {
        "name": "Borno",
        "region": "North East",
        "portal": "https://bornostate.gov.ng/",
        "website": "https://bornostate.gov.ng/",
        "2025": {
            "total": "₦615.86 billion",
            "status": "SIGNED"
        },
        "2026": {
            "total": "₦892.45 billion",
            "status": "SIGNED",
            "name": "Budget of Sustained Recovery and Growth",
            "education": "₦135.43 billion (highest allocation)"
        }
    },

    "gombe": {
        "name": "Gombe",
        "region": "North East",
        "portal": "https://gombestate.gov.ng/",
        "website": "https://gombestate.gov.ng/",
        "2025": {
            "total": "₦246.2 billion",
            "status": "SIGNED"
        },
        "2026": {
            "total": "TBD",
            "status": "SIGNED",
            "docs": {
                "approved": "https://www.mof.gm.gov.ng/wp-content/uploads/2026/01/Gombe-State-2026-Budget.pdf"
            }
        }
    },

    "taraba": {
        "name": "Taraba",
        "region": "North East",
        "portal": "https://tarabastate.gov.ng/",
        "website": "https://tarabastate.gov.ng/",
        "2025": {
            "total": "₦268.3 billion",
            "status": "SIGNED"
        },
        "2026": {
            "total": "₦650 billion",
            "status": "SIGNED",
            "education": "₦131.6 billion (20%)",
            "docs": {
                "mda_template": "https://mfbep.tr.gov.ng/2026-mda-budget-template/"
            }
        }
    },

    "yobe": {
        "name": "Yobe",
        "region": "North East",
        "portal": "https://yobestate.gov.ng/",
        "website": "https://yobestate.gov.ng/",
        "2025": {
            "total": "₦268.7 billion",
            "status": "SIGNED",
            "docs": {
                "approved": "https://budget.pfm.yb.gov.ng/wp-content/uploads/2025/01/Yobe-State-FY-2025-Budget-Publication-Printout-2.pdf"
            }
        },
        "2026": {
            "total": "₦515 billion",
            "status": "SIGNED",
            "social_services": "₦200 billion"
        }
    },

    # =========================================================================
    # NORTH CENTRAL (6 States + FCT)
    # =========================================================================
    "niger": {
        "name": "Niger",
        "region": "North Central",
        "portal": "https://nigerstate.gov.ng/",
        "website": "https://nigerstate.gov.ng/",
        "2025": {
            "total": "₦1.56 trillion",
            "status": "SIGNED",
            "note": "153.7% increase from 2024"
        },
        "2026": {
            "total": "₦1.073 trillion",
            "status": "SIGNED",
            "docs": {
                "budgetpedia": "https://budgetpedia.ng/approved-budget/"
            }
        }
    },

    "kwara": {
        "name": "Kwara",
        "region": "North Central",
        "portal": "https://kwarastate.gov.ng/",
        "website": "https://kwarastate.gov.ng/",
        "2025": {
            "total": "₦306.7 billion",
            "status": "SIGNED",
            "docs": {
                "approved": "https://kwarastate.gov.ng/wp-content/uploads/Kwara-State-Approved-Budget-FY-2025.pdf",
                "proposed": "https://kwarastate.gov.ng/wp-content/uploads/2025-Proposed-Budget-Executive.pdf"
            }
        },
        "2026": {
            "total": "₦644 billion",
            "status": "SIGNED",
            "social_services": "₦152.33 billion"
        }
    },

    "kogi": {
        "name": "Kogi",
        "region": "North Central",
        "portal": "https://kogistate.gov.ng/",
        "website": "https://kogistate.gov.ng/",
        "2025": {
            "total": "₦582.4 billion",
            "status": "SIGNED"
        },
        "2026": {
            "total": "₦820.49 billion",
            "status": "SIGNED",
            "education": "₦145.26 billion (18%)",
            "docs": {
                "call_circular": "https://kogistate.gov.ng/wp-content/uploads/2026-Budget-Call-Circular.pdf"
            }
        }
    },

    "benue": {
        "name": "Benue",
        "region": "North Central",
        "portal": "https://www.benueplanning.be.gov.ng/",
        "website": "https://benuestate.gov.ng/",
        "2025": {
            "total": "₦550.11 billion",
            "status": "SIGNED",
            "name": "Budget of Human Capital Development, Food Security, Digital Economy",
            "docs": {
                "documents_page": "https://www.benueplanning.be.gov.ng/budgets/"
            }
        },
        "2026": {
            "total": "TBD",
            "status": "SIGNED"
        }
    },

    "plateau": {
        "name": "Plateau",
        "region": "North Central",
        "portal": "https://plateaustate.gov.ng/",
        "website": "https://plateaustate.gov.ng/",
        "2025": {
            "total": "₦433.3 billion",
            "status": "SIGNED",
            "docs": {
                "approved_2023": "https://www.plateaustate.gov.ng/uploads/plateau-state-2023-approved-budget.pdf",
                "mtef": "https://www.plateaustate.gov.ng/uploads/Plateau_State_2024-2026_Medium_Term_Expenditure_Framework.docx"
            }
        },
        "2026": {
            "total": "₦914.86 billion",
            "status": "SIGNED",
            "capital": "₦573.4 billion (62.93%)",
            "social_services": "₦119 billion",
            "docs": {
                "portal": "https://www.plateaustate.gov.ng/"
            }
        }
    },

    "nasarawa": {
        "name": "Nasarawa",
        "region": "North Central",
        "portal": "https://nasarawastate.gov.ng/download-category/state-budget/",
        "website": "https://nasarawastate.gov.ng/",
        "2025": {
            "total": "₦318.4 billion",
            "status": "SIGNED",
            "docs": {
                "approved": "https://nasarawastate.gov.ng/wp-content/uploads/2025/01/NASARAWA-State-FY-2025-Budget-Publication.pdf"
            }
        },
        "2026": {
            "total": "₦545.2 billion",
            "status": "SIGNED",
            "education": "₦92.91 billion (17%)"
        }
    },

    "fct": {
        "name": "FCT Abuja",
        "region": "North Central",
        "portal": "https://budgetoffice.gov.ng/",
        "website": "https://fcta.gov.ng/",
        "2025": {
            "total": "₦1.78 trillion",
            "status": "SIGNED",
            "note": "Part of Federal Budget",
            "docs": {
                "fct_budget": "https://www.fcta.gov.ng/cat_doc/fct-budget/",
                "budget_office": "https://budgetoffice.gov.ng/index.php/resources/internal-resources/budget-documents"
            }
        },
        "2026": {
            "total": "₦460.73 billion",
            "status": "SIGNED",
            "note": "Included in Federal Budget",
            "docs": {
                "fct_budget": "https://www.fcta.gov.ng/cat_doc/fct-budget/",
                "budget_office": "https://budgetoffice.gov.ng/index.php/resources/internal-resources/budget-documents"
            }
        }
    }
}


def get_all_doc_urls():
    """Extract all document URLs from the database"""
    urls = []
    for state_key, state in STATES.items():
        for year in ["2025", "2026"]:
            if year in state:
                docs = state[year].get("docs", {})
                for doc_type, url in docs.items():
                    if url.endswith(".pdf"):
                        urls.append({
                            "state": state["name"],
                            "year": year,
                            "type": doc_type,
                            "url": url
                        })
    return urls


def print_summary():
    """Print comprehensive summary"""
    print("=" * 80)
    print("NIGERIAN STATE BUDGETS 2025 & 2026 - COMPLETE DATABASE")
    print("=" * 80)
    print(f"Last Updated: January 30, 2026")
    print()

    # Federal
    print("FEDERAL GOVERNMENT")
    print("-" * 40)
    print(f"  2025: {FEDERAL['2025']['total']} ({FEDERAL['2025']['status']})")
    print(f"  2026: {FEDERAL['2026']['total']} ({FEDERAL['2026']['status']})")
    print()

    # By region
    regions = {}
    for key, state in STATES.items():
        region = state["region"]
        if region not in regions:
            regions[region] = []
        regions[region].append((key, state))

    for region in ["South West", "South South", "South East", "North West", "North East", "North Central"]:
        states = regions.get(region, [])
        print(f"\n{region.upper()} ({len(states)} states)")
        print("-" * 60)
        for key, state in states:
            b2025 = state.get("2025", {}).get("total", "TBD")
            b2026 = state.get("2026", {}).get("total", "TBD")
            s2026 = state.get("2026", {}).get("status", "?")
            print(f"  {state['name']:15} | 2025: {b2025:20} | 2026: {b2026:20} ({s2026})")


def get_pending_2026():
    """Get states that haven't presented 2026 budget"""
    pending = []
    for key, state in STATES.items():
        status = state.get("2026", {}).get("status", "")
        if status in ["PENDING", "NOT YET PRESENTED"]:
            pending.append(state["name"])
    return pending


def export_csv():
    """Export to CSV format"""
    lines = ["state,region,2025_total,2025_status,2026_total,2026_status,portal"]
    for key, state in STATES.items():
        b2025 = state.get("2025", {}).get("total", "").replace(",", "")
        s2025 = state.get("2025", {}).get("status", "")
        b2026 = state.get("2026", {}).get("total", "").replace(",", "")
        s2026 = state.get("2026", {}).get("status", "")
        portal = state.get("portal", "")
        lines.append(f'{state["name"]},{state["region"]},{b2025},{s2025},{b2026},{s2026},{portal}')
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print_summary()
        print("\n" + "=" * 80)
        print("STATES WITHOUT 2026 BUDGET:")
        for s in get_pending_2026():
            print(f"  - {s}")
        print("\n" + "=" * 80)
        print("AVAILABLE PDF DOCUMENTS:")
        for doc in get_all_doc_urls():
            print(f"  [{doc['state']} {doc['year']}] {doc['type']}: {doc['url']}")
    elif sys.argv[1] == "csv":
        print(export_csv())
    elif sys.argv[1] == "pending":
        print("States without 2026 budget:")
        for s in get_pending_2026():
            print(f"  - {s}")
    elif sys.argv[1] == "urls":
        for doc in get_all_doc_urls():
            print(doc['url'])
