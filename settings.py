# ─────────────────────────────────────────────────────────────────────────────
# settings.py — Trust in Human-AI Teams (v6 — Option A: role-allocation redesign)
#
# FOUR PARAMETERS control the experiment design:
#
#   has_ai         : True | False
#                    True  → AI recommendation system is present (all configs below)
#                    False → HUMAN CONTROL condition: no AI at all. SA decides first
#                            (CSR-only), PA decides second (purchasing + SA's choice)
#                            and renders the team's final choice. transparency /
#                            augmented_role / accuracy_mode are ignored when has_ai=False.
#
#   transparency   : 'high' | 'low'
#                    High → AI explains reasoning + shows weights + score table
#                    Low  → AI gives recommendation only, no explanation
#
#   augmented_role : 'principal' | 'agent'
#                    principal → SA (who decides first) reviews the AI's
#                                recommendation; PA then reviews SA's decision with
#                                NO AI, and renders the final choice.
#                    agent     → SA submits an independent, CSR-only decision with
#                                no AI; PA then reviews SA's decision AND the AI's
#                                recommendation, and renders the final choice.
#                    In neither case is the non-augmented partner told the other's
#                    decision involved AI (blinded — see __init__.py docstring).
#                    REPLACES the retired 'ai_position' ('first'/'middle') variable,
#                    which controlled WHEN within one role's own judgment AI
#                    appeared. augmented_role instead controls WHICH role is
#                    exposed to AI at all.
#
#   accuracy_mode  : 'fixed' | 'manipulation'
#                    fixed        → draw per round (true 70% average, not manipulated)
#                    manipulation → draw once per session (always correct or always wrong)
#
#   sync           : True | False
#                    True  → Lab setting: WaitPages active, both players online together
#                    False → Online setting: WaitPages skipped, async delivery
#
# CURRENT PLAN: 2×2 design (transparency × augmented_role), accuracy_mode='fixed'
#   → Use the 4 sessions marked ★ MAIN below
#
# CONTROL: 'lab_control' / 'online_control' (has_ai=False) — human-only baseline.
#
# ALL 8 AI COMBINATIONS + 2 CONTROL CONFIGS are defined for flexibility.
# ─────────────────────────────────────────────────────────────────────────────

SESSION_CONFIGS = [

    # ══════════════════════════════════════════════════════════════
    # HUMAN CONTROL — no AI at all (baseline)
    # ══════════════════════════════════════════════════════════════

    dict(
        name='lab_control',
        display_name='◻ Control | Lab | No AI',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=False,
        sync=True,
    ),
    dict(
        name='online_control',
        display_name='◻ Control | Online | No AI',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=False,
        sync=False,
    ),

    # ══════════════════════════════════════════════════════════════
    # ★ MAIN — Lab, Fixed accuracy (2×2 design: Transparency × Role Allocation)
    # ══════════════════════════════════════════════════════════════

    dict(
        name='lab_principal_high',
        display_name='★ Lab | Principal-augmented | High Transparency | Fixed Accuracy',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='high',
        augmented_role='principal',
        accuracy_mode='fixed',
        sync=True,
    ),
    dict(
        name='lab_principal_low',
        display_name='★ Lab | Principal-augmented | Low Transparency | Fixed Accuracy',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='low',
        augmented_role='principal',
        accuracy_mode='fixed',
        sync=True,
    ),
    dict(
        name='lab_agent_high',
        display_name='★ Lab | Agent-augmented | High Transparency | Fixed Accuracy',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='high',
        augmented_role='agent',
        accuracy_mode='fixed',
        sync=True,
    ),
    dict(
        name='lab_agent_low',
        display_name='★ Lab | Agent-augmented | Low Transparency | Fixed Accuracy',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='low',
        augmented_role='agent',
        accuracy_mode='fixed',
        sync=True,
    ),

    # ══════════════════════════════════════════════════════════════
    # Online versions (async) — same 2×2 design
    # ══════════════════════════════════════════════════════════════

    dict(
        name='online_principal_high',
        display_name='Online | Principal-augmented | High Transparency | Fixed Accuracy',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='high',
        augmented_role='principal',
        accuracy_mode='fixed',
        sync=False,
    ),
    dict(
        name='online_principal_low',
        display_name='Online | Principal-augmented | Low Transparency | Fixed Accuracy',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='low',
        augmented_role='principal',
        accuracy_mode='fixed',
        sync=False,
    ),
    dict(
        name='online_agent_high',
        display_name='Online | Agent-augmented | High Transparency | Fixed Accuracy',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='high',
        augmented_role='agent',
        accuracy_mode='fixed',
        sync=False,
    ),
    dict(
        name='online_agent_low',
        display_name='Online | Agent-augmented | Low Transparency | Fixed Accuracy',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='low',
        augmented_role='agent',
        accuracy_mode='fixed',
        sync=False,
    ),

    # ══════════════════════════════════════════════════════════════
    # Accuracy Manipulation versions (Paper 2 — reliability consistency)
    # ══════════════════════════════════════════════════════════════

    dict(
        name='lab_principal_high_manip',
        display_name='Lab | Principal-augmented | High Transparency | Accuracy Manipulation',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='high',
        augmented_role='principal',
        accuracy_mode='manipulation',
        sync=True,
    ),
    dict(
        name='lab_principal_low_manip',
        display_name='Lab | Principal-augmented | Low Transparency | Accuracy Manipulation',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='low',
        augmented_role='principal',
        accuracy_mode='manipulation',
        sync=True,
    ),
    dict(
        name='lab_agent_high_manip',
        display_name='Lab | Agent-augmented | High Transparency | Accuracy Manipulation',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='high',
        augmented_role='agent',
        accuracy_mode='manipulation',
        sync=True,
    ),
    dict(
        name='lab_agent_low_manip',
        display_name='Lab | Agent-augmented | Low Transparency | Accuracy Manipulation',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='low',
        augmented_role='agent',
        accuracy_mode='manipulation',
        sync=True,
    ),
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00,
    participation_fee=10.00,   # € fixed participation fee (+ up to €5 performance bonus = €10-15 total, per consent form)
)

LANGUAGE_CODE = 'en'
REAL_WORLD_CURRENCY_CODE = 'EUR'
USE_POINTS = False

ROOMS = []

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'mypassword'   # change before deployment

SECRET_KEY = 'my-very-secret-key-12345-change-this-in-production'
