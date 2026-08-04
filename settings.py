# ─────────────────────────────────────────────────────────────────────────────
# settings.py — Trust in Human-AI Teams (v5)
#
# THREE PARAMETERS control the experiment design:
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
# ALL 8 COMBINATIONS are defined for flexibility.
# ─────────────────────────────────────────────────────────────────────────────

SESSION_CONFIGS = [

    # ══════════════════════════════════════════════════════════════
    # ★ MAIN — Lab, First position, Fixed accuracy (2×2 design)
    # ══════════════════════════════════════════════════════════════

    dict(
        name='lab_first_high',
        display_name='★ Lab | First | High Transparency | Fixed Accuracy',
        app_sequence=['supplier_selection'],
        num_demo_participants=2,
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
        transparency='low',
        ai_position='middle',
        accuracy_mode='manipulation',
        sync=True,
    ),
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00,
    participation_fee=8.00,   # € fixed participation fee
)

LANGUAGE_CODE = 'en'
REAL_WORLD_CURRENCY_CODE = 'EUR'
USE_POINTS = False

ROOMS = []

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'mypassword'   # change before deployment

SECRET_KEY = 'my-very-secret-key-12345-change-this-in-production'
