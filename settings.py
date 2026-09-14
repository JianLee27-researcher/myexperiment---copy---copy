# ─────────────────────────────────────────────────────────────────────────────
# settings.py — Trust in Human-AI Teams (v5)
#
# FOUR PARAMETERS control the experiment design:
#
#   has_ai         : True | False
#                    True  → AI recommendation system is present (all configs below)
#                    False → HUMAN CONTROL condition: no AI at all. PA makes a single
#                            decision directly (no AIRecommendation page), passed to SA.
#                            transparency / ai_position / accuracy_mode are ignored
#                            (irrelevant) when has_ai=False.
#
#   transparency   : 'high' | 'low'
#                    High → AI explains reasoning + shows weights + score table
#                    Low  → AI gives recommendation only, no explanation
#
#   ai_position    : 'first' | 'middle'
#                    first  → AI → PA → SA
#                    middle → PA(initial) → AI → PA(revised) → SA
#
#   accuracy_mode  : 'fixed' | 'manipulation'
#                    fixed        → draw per round (true 70% average, not manipulated)
#                    manipulation → draw once per session (always correct or always wrong)
#
#   sync           : True | False
#                    True  → Lab setting: WaitPages active, both players online together
#                    False → Online setting: WaitPages skipped, async delivery
#
# CURRENT PLAN: 2×2 design (transparency × position), accuracy_mode='fixed'
#   → Use the 4 sessions marked ★ MAIN below
#
# CONTROL: 'lab_control' / 'online_control' (has_ai=False) — human-only baseline,
#   structurally comparable to the 'first' AI-position condition (single PA decision).
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
    # ★ MAIN — Lab, First position, Fixed accuracy (2×2 design)
    # ══════════════════════════════════════════════════════════════

    dict(
        name='lab_first_high',
        display_name='★ Lab | First | High Transparency | Fixed Accuracy',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='high',
        ai_position='first',
        accuracy_mode='fixed',
        sync=True,
    ),
    dict(
        name='lab_first_low',
        display_name='★ Lab | First | Low Transparency | Fixed Accuracy',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='low',
        ai_position='first',
        accuracy_mode='fixed',
        sync=True,
    ),
    dict(
        name='lab_middle_high',
        display_name='★ Lab | Middle | High Transparency | Fixed Accuracy',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='high',
        ai_position='middle',
        accuracy_mode='fixed',
        sync=True,
    ),
    dict(
        name='lab_middle_low',
        display_name='★ Lab | Middle | Low Transparency | Fixed Accuracy',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='low',
        ai_position='middle',
        accuracy_mode='fixed',
        sync=True,
    ),

    # ══════════════════════════════════════════════════════════════
    # Online versions (async) — same 2×2 design
    # ══════════════════════════════════════════════════════════════

    dict(
        name='online_first_high',
        display_name='Online | First | High Transparency | Fixed Accuracy',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='high',
        ai_position='first',
        accuracy_mode='fixed',
        sync=False,
    ),
    dict(
        name='online_first_low',
        display_name='Online | First | Low Transparency | Fixed Accuracy',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='low',
        ai_position='first',
        accuracy_mode='fixed',
        sync=False,
    ),
    dict(
        name='online_middle_high',
        display_name='Online | Middle | High Transparency | Fixed Accuracy',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='high',
        ai_position='middle',
        accuracy_mode='fixed',
        sync=False,
    ),
    dict(
        name='online_middle_low',
        display_name='Online | Middle | Low Transparency | Fixed Accuracy',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='low',
        ai_position='middle',
        accuracy_mode='fixed',
        sync=False,
    ),

    # ══════════════════════════════════════════════════════════════
    # Accuracy Manipulation versions (if accuracy becomes 3rd IV)
    # ══════════════════════════════════════════════════════════════

    dict(
        name='lab_first_high_manip',
        display_name='Lab | First | High Transparency | Accuracy Manipulation',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='high',
        ai_position='first',
        accuracy_mode='manipulation',
        sync=True,
    ),
    dict(
        name='lab_first_low_manip',
        display_name='Lab | First | Low Transparency | Accuracy Manipulation',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='low',
        ai_position='first',
        accuracy_mode='manipulation',
        sync=True,
    ),
    dict(
        name='lab_middle_high_manip',
        display_name='Lab | Middle | High Transparency | Accuracy Manipulation',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='high',
        ai_position='middle',
        accuracy_mode='manipulation',
        sync=True,
    ),
    dict(
        name='lab_middle_low_manip',
        display_name='Lab | Middle | Low Transparency | Accuracy Manipulation',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
        has_ai=True,
        transparency='low',
        ai_position='middle',
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
