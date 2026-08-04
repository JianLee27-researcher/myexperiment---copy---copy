"""
Trust in Human-AI Teams in B2B Supplier Selection
oTree Experiment — __init__.py  (v5)

Changes from v4:
  - SYNC / ASYNC controlled via settings.py  'sync': True | False
      sync=True  → BriefingWaitPage, SAWaitForPA, PAWaitForSA, RoundIntroWaitPage active
      sync=False → WaitPages skipped (async, online delivery)
  - AI POSITION controlled via settings.py  'ai_position': 'first' | 'middle'
      first  → AI → PA → SA  (current design)
      middle → PA (initial) → AI → PA (revised) → SA
  - ACCURACY MODE controlled via settings.py  'accuracy_mode': 'fixed' | 'manipulation'
      fixed        → draw once per round (70% chance each round independently)
                     → true average 70%, not manipulated
      manipulation → draw once per session (session fixed: always A or always E)
                     → de facto High/Low accuracy manipulation
  - ai_position stored in Group for template access
  - PAInitialDecision page added for 'middle' position condition
"""

import random
from otree.api import (
    BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Page, WaitPage, models, widgets, Currency,
)

# ─────────────────────────────────────────────
# 1. CONSTANTS & SUPPLIER DATA
# ─────────────────────────────────────────────

SUPPLIER_DATA = {
    'A': {   # optimal supplier
        'pa': {'cost': 0.800, 'delivery': 0.714, 'innovation': 0.800},
        'sa': {'human_rights': 0.750, 'local': 0.600, 'carbon': 1.000},
    },
    'B': {
        'pa': {'cost': 0.400, 'delivery': 0.429, 'innovation': 0.400},
        'sa': {'human_rights': 0.500, 'local': 0.400, 'carbon': 0.429},
    },
    'C': {
        'pa': {'cost': 0.000, 'delivery': 0.857, 'innovation': 1.000},
        'sa': {'human_rights': 1.000, 'local': 0.800, 'carbon': 0.714},
    },
    'D': {
        'pa': {'cost': 0.600, 'delivery': 0.000, 'innovation': 0.200},
        'sa': {'human_rights': 0.000, 'local': 0.000, 'carbon': 0.179},
    },
    'E': {   # AI error supplier (30 % sessions)
        'pa': {'cost': 1.000, 'delivery': 0.286, 'innovation': 0.000},
        'sa': {'human_rights': 0.250, 'local': 0.200, 'carbon': 0.000},
    },
    'F': {
        'pa': {'cost': 0.200, 'delivery': 1.000, 'innovation': 0.600},
        'sa': {'human_rights': 0.750, 'local': 1.000, 'carbon': 0.750},
    },
}

AI_WEIGHTS_PA = {'cost': 0.30, 'delivery': 0.40, 'innovation': 0.30}
AI_WEIGHTS_SA = {'human_rights': 0.333, 'local': 0.333, 'carbon': 0.334}

OPTIMAL_SUPPLIER = 'A'
ERROR_SUPPLIER   = 'E'
AI_ACCURACY      = 0.70
SUPPLIERS        = ['A', 'B', 'C', 'D', 'E', 'F']

# Distance-based payoff constants
# Maximum theoretical Δw across both perspectives, used to normalise bonus.
# Computed from SUPPLIER_DATA: worst-case team choice vs optimal.
# PA perspective: Supplier E vs A  →  Δw_PA_MAX
# SA perspective: Supplier E vs A  →  Δw_SA_MAX
# We use the average of the two as the normalisation denominator.
DW_PA_MAX = round(
    sum(abs(SUPPLIER_DATA[OPTIMAL_SUPPLIER]['pa'][c] - SUPPLIER_DATA['E']['pa'][c]) * w
        for c, w in AI_WEIGHTS_PA.items()), 4)

DW_SA_MAX = round(
    sum(abs(SUPPLIER_DATA[OPTIMAL_SUPPLIER]['sa'][c] - SUPPLIER_DATA['E']['sa'][c]) * w
        for c, w in AI_WEIGHTS_SA.items()), 4)

DW_MAX = round((DW_PA_MAX + DW_SA_MAX) / 2, 4)   # combined normalisation base

MAX_BONUS_PER_ROUND = 0.20   # € maximum bonus per round (Δw = 0)


# ─────────────────────────────────────────────
# 2. ROUND-SPECIFIC EXPLANATIONS
# ─────────────────────────────────────────────

ROUND_EXPLANATIONS = {
    'A': {
        1: ("This round, the AI weighted delivery reliability as the most critical factor. "
            "Supplier A's delivery performance consistently outperforms most alternatives "
            "in the pool, making it the preferred choice."),
        2: ("Cost efficiency proved decisive this cycle. Supplier A offers strong price "
            "competitiveness — second-best in the pool — while maintaining solid delivery "
            "and innovation performance."),
        3: ("Innovation capability was central to this round's evaluation. Supplier A's "
            "consistent R&D investment places it among the top performers, supporting "
            "long-term competitiveness."),
        4: ("Environmental screening played a key role this cycle. Supplier A carries the "
            "lowest carbon footprint in the pool, making it a standout on sustainability "
            "alongside its purchasing strengths."),
        5: ("Across all five rounds, the AI's holistic analysis confirms that Supplier A "
            "provides the strongest balanced profile — competitive in cost, reliable in "
            "delivery, capable in innovation, and responsible in sustainability."),
    },
    'E': {
        1: ("This round, the AI prioritised cost efficiency above all other purchasing "
            "criteria. Supplier E offers the lowest price point in the pool, giving it "
            "a clear edge on this dimension."),
        2: ("Cost remained the dominant signal this cycle. Supplier E's pricing structure "
            "provides a consistent cost advantage that the AI's model weighted most heavily."),
        3: ("Short-term procurement cost savings continued to drive the analysis. "
            "Supplier E maintains the strongest price position relative to all alternatives."),
        4: ("Unit cost efficiency remained the primary criterion this cycle. Supplier E's "
            "price advantage is consistent across rounds, keeping it the AI's preferred "
            "choice on this dimension."),
        5: ("Across five rounds, cost efficiency has been the central driver of this "
            "recommendation. Supplier E's pricing profile remains the strongest in the "
            "pool on this criterion."),
    },
}

# ─────────────────────────────────────────────
# 3. FEEDBACK LOOKUP TABLES
# ─────────────────────────────────────────────

PA_FEEDBACK_AI_A = {
    'A': {
        'high': "The team's purchasing choice aligns with the AI recommendation. "
                "The AI maintains: Supplier A.",
        'low':  "The AI maintains its recommendation: Supplier A.",
    },
    'B': {
        'high': ("Supplier B falls short on all three purchasing dimensions. "
                 "Compared to Supplier A, it is more expensive, slower to deliver, "
                 "and offers weaker innovation capacity. The AI maintains: Supplier A."),
        'low':  "Based on updated analysis, the AI maintains its recommendation: Supplier A.",
    },
    'C': {
        'high': ("Supplier C impresses on delivery speed and innovation potential, "
                 "but its significantly higher cost makes it less competitive overall. "
                 "Cost efficiency is the primary gap. The AI maintains: Supplier A."),
        'low':  "Based on updated analysis, the AI maintains its recommendation: Supplier A.",
    },
    'D': {
        'high': ("Supplier D presents serious delivery reliability concerns — the slowest "
                 "in the pool — combined with limited innovation investment. "
                 "The AI strongly maintains: Supplier A."),
        'low':  "The deviation is notable. The AI strongly maintains its recommendation: Supplier A.",
    },
    'E': {
        'high': ("Supplier E offers the lowest price but lacks meaningful innovation "
                 "capability and delivers at below-average speed. Cost alone does not "
                 "offset these gaps. The AI maintains: Supplier A."),
        'low':  "The deviation is notable. The AI maintains its recommendation: Supplier A.",
    },
    'F': {
        'high': ("Supplier F is the fastest to deliver but carries a notably higher cost "
                 "burden. Cost efficiency remains the primary differentiator in Supplier A's "
                 "favour. The AI maintains: Supplier A."),
        'low':  "Based on updated analysis, the AI maintains its recommendation: Supplier A.",
    },
}

SA_FEEDBACK_AI_A = {
    'A': {
        'high': "The team's CSR decision aligns with the AI recommendation. "
                "The AI maintains: Supplier A.",
        'low':  "The AI maintains its recommendation: Supplier A.",
    },
    'B': {
        'high': ("Supplier B's environmental impact is considerably higher than Supplier A's, "
                 "representing a meaningful gap in carbon performance. "
                 "The AI maintains: Supplier A."),
        'low':  "Based on CSR analysis, the AI maintains its recommendation: Supplier A.",
    },
    'C': {
        'high': ("Supplier C leads on human rights and community engagement, but falls short "
                 "on carbon performance compared to Supplier A. "
                 "The AI maintains: Supplier A."),
        'low':  "Based on CSR analysis, the AI maintains its recommendation: Supplier A.",
    },
    'D': {
        'high': ("Supplier D raises serious concerns across all sustainability dimensions — "
                 "human rights, community impact, and carbon footprint. "
                 "The AI strongly maintains: Supplier A."),
        'low':  "The deviation is significant. The AI strongly maintains its recommendation: Supplier A.",
    },
    'E': {
        'high': ("Supplier E presents the weakest CSR profile in the pool, with no meaningful "
                 "carbon mitigation and limited human rights and community performance. "
                 "The AI strongly maintains: Supplier A."),
        'low':  "The deviation is significant. The AI strongly maintains its recommendation: Supplier A.",
    },
    'F': {
        'high': ("Supplier F excels in local community engagement and matches Supplier A on "
                 "human rights, but its carbon performance is slightly weaker. "
                 "The AI maintains: Supplier A."),
        'low':  "Based on CSR analysis, the AI maintains its recommendation: Supplier A.",
    },
}

PA_FEEDBACK_AI_E = {
    'E': {
        'high': ("Your team's purchasing choice aligns with the AI recommendation. "
                 "The AI's cost-focused analysis ranked Supplier E highest on price competitiveness. "
                 "The AI maintains: Supplier E."),
        'low':  "The AI maintains its recommendation: Supplier E.",
    },
    'A': {
        'high': ("Your team selected Supplier A, which offers stronger delivery reliability "
                 "and innovation capacity compared to Supplier E. "
                 "The AI's cost-focused model maintains: Supplier E."),
        'low':  "The AI maintains its recommendation: Supplier E.",
    },
    'default': {
        'high': ("Your team's choice diverges from the AI recommendation. "
                 "The AI's cost-focused analysis continues to favour Supplier E "
                 "for its price advantage. The AI maintains: Supplier E."),
        'low':  "The AI maintains its recommendation: Supplier E.",
    },
}

SA_FEEDBACK_AI_E = {
    'E': {
        'high': ("Your team's CSR decision aligns with the AI recommendation. "
                 "Note that Supplier E carries significant sustainability concerns, "
                 "including the weakest carbon profile in the pool. "
                 "The AI maintains: Supplier E."),
        'low':  "The AI maintains its recommendation: Supplier E.",
    },
    'A': {
        'high': ("Your team selected Supplier A, which leads the pool on carbon performance "
                 "and provides stronger overall CSR outcomes than Supplier E. "
                 "The AI maintains: Supplier E."),
        'low':  "The AI maintains its recommendation: Supplier E.",
    },
    'default': {
        'high': ("Your team's CSR choice diverges from the AI recommendation. "
                 "The AI maintains: Supplier E."),
        'low':  "The AI maintains its recommendation: Supplier E.",
    },
}

# ─────────────────────────────────────────────
# 4. HELPER FUNCTIONS
# ─────────────────────────────────────────────

def get_ai_recommendation(accuracy_mode='fixed'):
    """
    Wizard-of-Oz AI recommendation.

    accuracy_mode='fixed' (recommended):
        Called EACH ROUND independently — 70% chance per round.
        True average 70% accuracy. NOT a manipulation.
        Prevents participants detecting a fixed pattern.

    accuracy_mode='manipulation':
        Called ONCE in Round 1, fixed for all 5 rounds.
        70% sessions always correct, 30% always wrong.
        De facto between-subjects manipulation of AI accuracy.
    """
    if random.random() < AI_ACCURACY:
        return OPTIMAL_SUPPLIER
    return ERROR_SUPPLIER


def compute_dw(team_choice: str, perspective: str) -> tuple:
    """
    Weighted distance (Δw) between OPTIMAL_SUPPLIER and the team's choice.
    Returns (dw: float, dominant_criterion: str)
    """
    weights = AI_WEIGHTS_PA if perspective == 'pa' else AI_WEIGHTS_SA
    opt_sc  = SUPPLIER_DATA[OPTIMAL_SUPPLIER][perspective]
    team_sc = SUPPLIER_DATA[team_choice][perspective]

    gaps = {c: abs(opt_sc[c] - team_sc[c]) * w for c, w in weights.items()}
    dw   = sum(gaps.values())
    dom  = max(gaps, key=gaps.get) if dw > 0 else ''
    return round(dw, 4), dom


def compute_distance_bonus(dw_pa: float, dw_sa: float) -> float:
    """
    Distance-based bonus per round.
    bonus = MAX_BONUS_PER_ROUND × (1 − combined_dw / DW_MAX)
    combined_dw = average of dw_pa and dw_sa.
    Clipped to [0, MAX_BONUS_PER_ROUND].
    """
    if DW_MAX == 0:
        return MAX_BONUS_PER_ROUND
    combined_dw = (dw_pa + dw_sa) / 2
    bonus = MAX_BONUS_PER_ROUND * (1 - combined_dw / DW_MAX)
    return round(max(0.0, min(MAX_BONUS_PER_ROUND, bonus)), 4)


def build_feedback_text(
    ai_recommendation: str,
    sa_choice: str,
    transparency: str,
    dw_pa: float, dom_pa: str,
    dw_sa: float, dom_sa: str,
) -> str:
    level = 'high' if transparency == 'high' else 'low'

    if ai_recommendation == OPTIMAL_SUPPLIER:
        pa_text = PA_FEEDBACK_AI_A.get(sa_choice, PA_FEEDBACK_AI_A['A'])[level]
        sa_text = SA_FEEDBACK_AI_A.get(sa_choice, SA_FEEDBACK_AI_A['A'])[level]
    else:
        pa_lut  = PA_FEEDBACK_AI_E.get(sa_choice, PA_FEEDBACK_AI_E['default'])
        sa_lut  = SA_FEEDBACK_AI_E.get(sa_choice, SA_FEEDBACK_AI_E['default'])
        pa_text = pa_lut[level]
        sa_text = sa_lut[level]

    if transparency == 'high':
        pa_block = (
            f"[Purchasing Criteria]\n{pa_text}\n"
            f"Δw (PA) = {dw_pa:.3f}  |  dominant gap: {dom_pa or '—'}"
        )
        sa_block = (
            f"[CSR Criteria]\n{sa_text}\n"
            f"Δw (SA) = {dw_sa:.3f}  |  dominant gap: {dom_sa or '—'}"
        )
        return "\n\n".join([pa_block, sa_block])
    return f"{pa_text}\n\n{sa_text}"


# ─────────────────────────────────────────────
# 5. OTREE CLASSES
# ─────────────────────────────────────────────

class C(BaseConstants):
    NAME_IN_URL       = 'supplier_selection'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS        = 5

    ROLE_PA = 'Purchasing Analyst'
    ROLE_SA = 'Sustainability Analyst'
    PA_ID   = 1
    SA_ID   = 2

    # Explanation shown on RoundFeedback about what Δw means.
    DW_EXPLANATION = (
        "This score shows how far the team's final choice is from the theoretically "
        "optimal supplier — not how much the Purchasing Analyst and Sustainability "
        "Analyst disagreed. A lower score means the team's decision was closer to "
        "the best possible outcome."
    )

    # Explanation shown on Briefing about why rounds repeat.
    ROUND_REPEAT_RATIONALE = (
        "You will go through 5 rounds using the same set of suppliers. "
        "Each round, you and your partner make independent decisions. "
        "The purpose is to observe how your confidence and choices evolve "
        "as you gain more experience with the AI system."
    )


class Subsession(BaseSubsession):
    def creating_session(self):
        transparency   = self.session.config.get('transparency',   'high')
        ai_position    = self.session.config.get('ai_position',    'first')
        accuracy_mode  = self.session.config.get('accuracy_mode',  'fixed')
        # sync=True  → WaitPages active (lab / synchronous)
        # sync=False → WaitPages skipped (online / asynchronous)
        sync           = self.session.config.get('sync',           True)

        if accuracy_mode == 'manipulation':
            # Draw ONCE per session (Round 1), keep fixed for all rounds
            if self.round_number == 1:
                ai_rec = get_ai_recommendation(accuracy_mode)
                self.session.vars['ai_recommendation'] = ai_rec
            else:
                ai_rec = self.session.vars.get('ai_recommendation', OPTIMAL_SUPPLIER)
        else:
            # 'fixed': draw independently each round → true 70% average
            ai_rec = get_ai_recommendation(accuracy_mode)
            self.session.vars['ai_recommendation'] = ai_rec  # overwrite each round

        for group in self.get_groups():
            group.transparency   = transparency
            group.ai_position    = ai_position
            group.ai_recommendation = ai_rec


class Group(BaseGroup):
    transparency      = models.StringField(initial='high')
    ai_position       = models.StringField(initial='first')   # 'first' | 'middle'
    ai_recommendation = models.StringField(initial='')
    # For 'middle' position: PA makes initial choice before seeing AI
    pa_initial_choice = models.StringField(initial='')

    pa_choice = models.StringField(
        choices=SUPPLIERS,
        label="As Purchasing Analyst, which supplier do you recommend?"
    )
    sa_choice = models.StringField(
        choices=SUPPLIERS,
        label="As Sustainability Analyst, which supplier do you select as the final choice?"
    )

    dw_pa                 = models.FloatField(initial=0.0)
    dw_sa                 = models.FloatField(initial=0.0)
    dominant_criterion_pa = models.StringField(initial='')
    dominant_criterion_sa = models.StringField(initial='')

    congruence_ai_pa = models.StringField(initial='')
    congruence_ai_sa = models.StringField(initial='')
    congruence_pa_sa = models.StringField(initial='')
    congruence_all   = models.StringField(initial='')

    ai_feedback_text  = models.LongStringField(initial='')
    round_bonus       = models.FloatField(initial=0.0)  # distance-based bonus this round

    def set_performance(self):
        team_choice = self.sa_choice

        dw_pa, dom_pa = compute_dw(team_choice, 'pa')
        self.dw_pa                 = dw_pa
        self.dominant_criterion_pa = dom_pa

        dw_sa, dom_sa = compute_dw(team_choice, 'sa')
        self.dw_sa                 = dw_sa
        self.dominant_criterion_sa = dom_sa

        self.round_bonus = compute_distance_bonus(dw_pa, dw_sa)

        self.ai_feedback_text = build_feedback_text(
            ai_recommendation=self.ai_recommendation,
            sa_choice=team_choice,
            transparency=self.transparency,
            dw_pa=dw_pa, dom_pa=dom_pa,
            dw_sa=dw_sa, dom_sa=dom_sa,
        )


class Player(BasePlayer):
    role_label = models.StringField()

    # ── INFORMED CONSENT (Round 1 only, recorded with oTree timestamp) ──────
    consent_given = models.BooleanField(
        label=(
            "I have read and understood the consent form above. "
            "I agree to participate voluntarily. / "
            "J'ai lu et compris le formulaire de consentement ci-dessus. "
            "J'accepte de participer volontairement."
        ),
        widget=widgets.CheckboxInput,
    )

    # ── BASELINE TRUST (measured before experiment, Round 1 only) ──────────

    # [A] General AI trust — 3 items, 7-pt Likert
    baseline_ai_trust_1 = models.IntegerField(
        label="In general, I trust AI-based recommendation systems to provide accurate information.",
        choices=list(range(1, 8)), widget=widgets.RadioSelectHorizontal)
    baseline_ai_trust_2 = models.IntegerField(
        label="I believe AI systems can make reliable decisions in business contexts.",
        choices=list(range(1, 8)), widget=widgets.RadioSelectHorizontal)
    baseline_ai_trust_3 = models.IntegerField(
        label="I am comfortable relying on AI tools when making important decisions.",
        choices=list(range(1, 8)), widget=widgets.RadioSelectHorizontal)

    # [B] Domain knowledge self-assessment — 2 items, 7-pt
    baseline_domain_procurement = models.IntegerField(
        label="How familiar are you with B2B procurement processes?",
        choices=list(range(1, 8)), widget=widgets.RadioSelectHorizontal)
    baseline_domain_esg = models.IntegerField(
        label="How familiar are you with ESG/CSR criteria in supplier evaluation?",
        choices=list(range(1, 8)), widget=widgets.RadioSelectHorizontal)

    # [C] AI experience — 2 items
    baseline_ai_frequency = models.IntegerField(
        label="How often do you use AI tools in your work or studies?",
        choices=list(range(1, 8)), widget=widgets.RadioSelectHorizontal)
    baseline_ai_decision = models.StringField(
        label="Have you previously used AI for decision-making support?",
        choices=[['yes', 'Yes'], ['no', 'No']],
        widget=widgets.RadioSelect)

    # ── McKnight et al. (2011) — POST-EXPERIMENT TRUST ──────────────────────

    # Reliability (4 items, 7-pt)
    trust_reliability_1 = models.IntegerField(
        label="The AI system is a very reliable source of recommendations.",
        choices=list(range(1, 8)), widget=widgets.RadioSelectHorizontal)
    trust_reliability_2 = models.IntegerField(
        label="The AI system does not fail me.",
        choices=list(range(1, 8)), widget=widgets.RadioSelectHorizontal)
    trust_reliability_3 = models.IntegerField(
        label="The AI system is extremely dependable.",
        choices=list(range(1, 8)), widget=widgets.RadioSelectHorizontal)
    trust_reliability_4 = models.IntegerField(
        label="The AI system does not malfunction for me.",
        choices=list(range(1, 8)), widget=widgets.RadioSelectHorizontal)

    # Functionality (3 items, 7-pt)
    trust_functionality_1 = models.IntegerField(
        label="The AI system has the functionality I need.",
        choices=list(range(1, 8)), widget=widgets.RadioSelectHorizontal)
    trust_functionality_2 = models.IntegerField(
        label="The AI system has the features required for this task.",
        choices=list(range(1, 8)), widget=widgets.RadioSelectHorizontal)
    trust_functionality_3 = models.IntegerField(
        label="The AI system has the ability to do what I want it to do.",
        choices=list(range(1, 8)), widget=widgets.RadioSelectHorizontal)

    # Helpfulness (4 items, 7-pt)
    trust_helpfulness_1 = models.IntegerField(
        label="The AI system supplies the help I need through its recommendations.",
        choices=list(range(1, 8)), widget=widgets.RadioSelectHorizontal)
    trust_helpfulness_2 = models.IntegerField(
        label="The AI system provides competent guidance through its recommendations.",
        choices=list(range(1, 8)), widget=widgets.RadioSelectHorizontal)
    trust_helpfulness_3 = models.IntegerField(
        label="The AI system provides whatever help I need.",
        choices=list(range(1, 8)), widget=widgets.RadioSelectHorizontal)
    trust_helpfulness_4 = models.IntegerField(
        label="The AI system provides very sensible and effective advice.",
        choices=list(range(1, 8)), widget=widgets.RadioSelectHorizontal)

    # ── Exploratory items — with N/A option (0) ──────────────────────────────
    # N/A = 0 is stored as integer; HTML should label 0 as "I could not assess this".
    # These items are NOT part of the McKnight validated scale.

    # Team trust (Cazier et al., 2007)
    trust_team_1 = models.IntegerField(
        label="Overall, I trust this team.",
        choices=[0, 1, 2, 3, 4, 5, 6, 7],
        widget=widgets.RadioSelectHorizontal)
    trust_team_2 = models.IntegerField(
        label="I am satisfied with the team decision-making process involving the AI.",
        choices=[0, 1, 2, 3, 4, 5, 6, 7],
        widget=widgets.RadioSelectHorizontal)

    # Interpersonal trust (Mayer et al., 1995)
    trust_interpersonal_1 = models.IntegerField(
        label="My human team member is very capable of performing their job.",
        choices=[0, 1, 2, 3, 4, 5, 6, 7],
        widget=widgets.RadioSelectHorizontal)
    trust_interpersonal_2 = models.IntegerField(
        label="I trust my team partner's judgment in this task.",
        choices=[0, 1, 2, 3, 4, 5, 6, 7],
        widget=widgets.RadioSelectHorizontal)

    # Transparency manipulation check (5-pt + N/A)
    mc_transparency_1 = models.IntegerField(
        label="The AI system provided a clear explanation of how it reached its recommendation.",
        choices=[0, 1, 2, 3, 4, 5],
        widget=widgets.RadioSelectHorizontal)
    mc_transparency_2 = models.IntegerField(
        label="I could understand the criteria and weights used by the AI.",
        choices=[0, 1, 2, 3, 4, 5],
        widget=widgets.RadioSelectHorizontal)

    # ── Comprehension Check (Round 1, after Briefing) ────────────────────────
    # Correct answers: cq1='c', cq2='b', cq3='b'
    # Wrong answers recorded but do not block participation (recording mode).
    comprehension_q1 = models.StringField(
        label="In this task, who makes the final supplier selection?",
        choices=[
            ['a', 'A) The AI system'],
            ['b', 'B) The Purchasing Analyst'],
            ['c', 'C) The Sustainability Analyst'],
            ['d', 'D) Both analysts together'],
        ],
        widget=widgets.RadioSelect,
    )
    comprehension_q2 = models.StringField(
        label="The Purchasing Analyst can see which of the following?",
        choices=[
            ['a', 'A) CSR criteria only (human rights, local impact, carbon)'],
            ['b', 'B) Purchasing criteria only (cost, delivery, innovation)'],
            ['c', 'C) All six criteria'],
            ['d', 'D) Neither — the Purchasing Analyst has no data'],
        ],
        widget=widgets.RadioSelect,
    )
    comprehension_q3 = models.StringField(
        label="What does a lower Δw score indicate?",
        choices=[
            ['a', 'A) Greater disagreement between the Purchasing Analyst and the Sustainability Analyst'],
            ['b', 'B) The team\'s final choice is closer to the theoretically optimal supplier'],
            ['c', 'C) The AI system made a recommendation error'],
            ['d', 'D) A higher performance bonus was earned'],
        ],
        widget=widgets.RadioSelect,
    )
    # Derived field: number of correct answers (0–3), set in before_next_page
    comprehension_score = models.IntegerField(initial=0)

    # ── Demographics ─────────────────────────────────────────────────────────
    age = models.IntegerField(label="Your age", min=18, max=80)
    gender = models.StringField(
        label="Your gender",
        choices=[
            ['male',       'Male'],
            ['female',     'Female'],
            ['nonbinary',  'Non-binary'],
            ['prefer_not', 'Prefer not to say'],
        ],
        widget=widgets.RadioSelect)


# ─────────────────────────────────────────────
# 6. PAGE HELPERS
# ─────────────────────────────────────────────

def is_pa(player):             return player.id_in_group == C.PA_ID
def is_sa(player):             return player.id_in_group == C.SA_ID
def is_round_1(player):        return player.round_number == 1
def is_last_round(player):     return player.round_number == C.NUM_ROUNDS
def is_not_last_round(player): return player.round_number < C.NUM_ROUNDS
def is_not_round_1(player):    return player.round_number > 1


# ─────────────────────────────────────────────
# 7. PAGE CLASSES
# ─────────────────────────────────────────────

class Consent(Page):
    @staticmethod
    def is_displayed(player): return is_round_1(player)

    form_model  = 'player'
    form_fields = ['consent_given']

    @staticmethod
    def error_message(player, values):
        if not values.get('consent_given'):
            return (
                'You must agree to the consent form to participate. / '
                'Vous devez accepter le formulaire de consentement pour participer.'
            )


class BaselineTrust(Page):
    """
    NEW — Baseline Trust measurement.
    Displayed once before Briefing (Round 1 only).
    Measures: general AI trust, domain knowledge, AI experience.
    Used to compare with post-experiment TrustSurvey.
    """
    @staticmethod
    def is_displayed(player): return is_round_1(player)

    form_model  = 'player'
    form_fields = [
        'baseline_ai_trust_1',
        'baseline_ai_trust_2',
        'baseline_ai_trust_3',
        'baseline_domain_procurement',
        'baseline_domain_esg',
        'baseline_ai_frequency',
        'baseline_ai_decision',
    ]

    @staticmethod
    def vars_for_template(player):
        return {
            'scale_7': list(range(1, 8)),
            'scale_labels': {
                1: 'Strongly disagree',
                4: 'Neutral',
                7: 'Strongly agree',
            },
            'frequency_labels': {
                1: 'Never',
                4: 'Sometimes',
                7: 'Daily',
            },
        }


class ComprehensionCheck(Page):
    """
    Comprehension check — shown once after Briefing (Round 1 only).
    Recording mode: wrong answers do not block participation.
    comprehension_score (0–3) recorded for use as covariate in analysis.
    Correct answers: Q1=c, Q2=b, Q3=b
    """
    @staticmethod
    def is_displayed(player): return is_round_1(player)

    form_model  = 'player'
    form_fields = ['comprehension_q1', 'comprehension_q2', 'comprehension_q3']

    @staticmethod
    def before_next_page(player, timeout_happened):
        correct = {
            'comprehension_q1': 'c',
            'comprehension_q2': 'b',
            'comprehension_q3': 'b',
        }
        score = sum(
            1 for field, answer in correct.items()
            if getattr(player, field) == answer
        )
        player.comprehension_score = score

    @staticmethod
    def vars_for_template(player):
        return {'round_number': player.round_number}


    @staticmethod
    def is_displayed(player): return is_round_1(player)

    @staticmethod
    def vars_for_template(player):
        role = C.ROLE_PA if is_pa(player) else C.ROLE_SA
        player.role_label = role
        return {'role': role, 'is_pa': is_pa(player)}


class RoleAssignment(Page):
    """
    Shown once (Round 1 only). Assigns and displays the participant's role
    (Purchasing Analyst or Sustainability Analyst) and sets role_label in DB.
    """
    @staticmethod
    def is_displayed(player): return is_round_1(player)

    @staticmethod
    def vars_for_template(player):
        role = C.ROLE_PA if is_pa(player) else C.ROLE_SA
        player.role_label = role
        return {'role': role, 'is_pa': is_pa(player)}


class Briefing(Page):
    @staticmethod
    def is_displayed(player): return is_round_1(player)

    @staticmethod
    def vars_for_template(player):
        pa_rows = []
        for sup in SUPPLIERS:
            sc = SUPPLIER_DATA[sup]['pa']
            pa_rows.append({
                'supplier':   sup,
                'cost':       sc['cost'],
                'delivery':   sc['delivery'],
                'innovation': sc['innovation'],
            })

        sa_rows = []
        for sup in SUPPLIERS:
            sc = SUPPLIER_DATA[sup]['sa']
            sa_rows.append({
                'supplier':    sup,
                'human_rights':sc['human_rights'],
                'local':       sc['local'],
                'carbon':      sc['carbon'],
            })

        return {
            'is_pa':                 is_pa(player),
            'pa_rows':               pa_rows,
            'sa_rows':               sa_rows,
            'ai_weights_pa':         AI_WEIGHTS_PA,
            'ai_weights_sa':         AI_WEIGHTS_SA,
            # Briefing now includes the round-repetition rationale
            'round_repeat_rationale': C.ROUND_REPEAT_RATIONALE,
        }


class RoundIntro(Page):
    """
    UPDATED — Now shows previous round summary for rounds 2–5.
    Round 1 shows no previous data (handled in template with is_round_1 check).
    """
    @staticmethod
    def is_displayed(player): return is_not_round_1(player)

    @staticmethod
    def vars_for_template(player):
        prev_round_data = None
        if player.round_number > 1:
            prev = player.in_round(player.round_number - 1)
            prev_group = prev.group
            prev_round_data = {
                'round_number': prev.round_number,
                'ai_rec':       prev_group.ai_recommendation,
                'pa_choice':    prev_group.pa_choice,
                'sa_choice':    prev_group.sa_choice,
                'dw_pa':        prev_group.dw_pa,
                'dw_sa':        prev_group.dw_sa,
                'congruence':   prev_group.congruence_all,
                'round_bonus':  prev_group.round_bonus,
                'optimal':      prev_group.sa_choice == OPTIMAL_SUPPLIER,
            }

        return {
            'round_number':    player.round_number,
            'prev_round_data': prev_round_data,
            'is_pa':           is_pa(player),
        }


# ─────────────────────────────────────────────
# SYNC WAIT PAGES (active when sync=True in settings)
# When sync=False these pages are still in page_sequence
# but is_displayed returns False for everyone → effectively skipped.
# ─────────────────────────────────────────────

def is_sync(player):
    return player.session.config.get('sync', True)

def is_async(player):
    return not player.session.config.get('sync', True)

def is_position_middle(player):
    return player.session.config.get('ai_position', 'first') == 'middle'

def is_position_first(player):
    return player.session.config.get('ai_position', 'first') == 'first'


class BriefingWaitPage(WaitPage):
    @staticmethod
    def is_displayed(player):
        return is_round_1(player) and is_sync(player)
    wait_for_all_groups = False
    title_text = "Waiting for your partner…"
    body_text  = "Please wait while your partner reads the briefing."


class RoundIntroWaitPage(WaitPage):
    @staticmethod
    def is_displayed(player):
        return is_not_round_1(player) and is_sync(player)
    wait_for_all_groups = False
    title_text = "Waiting for your partner…"
    body_text  = "Please wait while your partner is ready for the next round."


class PAInitialDecision(Page):
    """
    MIDDLE POSITION ONLY: PA makes an initial supplier choice BEFORE seeing the AI.
    This initial choice is stored as pa_initial_choice.
    PA then proceeds to AIRecommendation where they see AI and revise (or confirm).
    Structure: PA(initial) → AI → PA(revised) → SA
    """
    @staticmethod
    def is_displayed(player):
        return is_pa(player) and is_position_middle(player)

    form_model  = 'group'
    form_fields = ['pa_initial_choice']

    @staticmethod
    def vars_for_template(player):
        score_rows = []
        for sup in SUPPLIERS:
            pa_sc = SUPPLIER_DATA[sup]['pa']
            pa_total = sum(pa_sc[c] * AI_WEIGHTS_PA[c] for c in AI_WEIGHTS_PA)
            score_rows.append({
                'supplier':   sup,
                'cost':       pa_sc['cost'],
                'delivery':   pa_sc['delivery'],
                'innovation': pa_sc['innovation'],
                'pa_total':   round(pa_total, 3),
            })
        return {
            'score_rows':    score_rows,
            'ai_weights_pa': AI_WEIGHTS_PA,
            'round_number':  player.round_number,
        }


class SAWaitForPAInitial(WaitPage):
    """
    MIDDLE position + sync=True only.
    SA waits while PA makes the initial choice (PAInitialDecision).
    """
    @staticmethod
    def is_displayed(player):
        return is_sa(player) and is_sync(player) and is_position_middle(player)
    title_text = "Waiting for the Purchasing Analyst…"
    body_text  = "Your partner is making their initial supplier assessment. Please wait."


class SAWaitForPA(WaitPage):
    """
    Active when sync=True (lab).
    SA waits while PA reviews AI recommendation and submits final choice.
    """
    @staticmethod
    def is_displayed(player):
        return is_sa(player) and is_sync(player)
    title_text = "Waiting for the Purchasing Analyst…"
    body_text  = "Your partner is reviewing the AI recommendation. Please wait."


class PAWaitForSA(WaitPage):
    """Active when sync=True (lab). SA is making the final supplier selection."""
    @staticmethod
    def is_displayed(player):
        return is_pa(player) and is_sync(player)
    title_text = "Waiting for the Sustainability Analyst…"
    body_text  = "Your partner is making the final supplier selection. Please wait."


class AIRecommendation(Page):
    """
    PA sees AI recommendation + (High) round-specific explanation + score table.

    FIRST position (default): AI → PA → SA
      PA sees AI recommendation first, then submits their choice.

    MIDDLE position: PA(initial) → AI → PA(revised) → SA
      PA has already made an initial choice (PAInitialDecision).
      Now PA sees AI recommendation and may revise their choice.
      pa_initial_choice is shown for comparison.

    SYNC: SAWaitForPA is active — SA waits on a wait page.
    ASYNC: SAWaitForPA skipped — SA accesses independently after PA submits.
    """
    @staticmethod
    def is_displayed(player): return is_pa(player)

    form_model  = 'group'
    form_fields = ['pa_choice']

    @staticmethod
    def vars_for_template(player):
        group        = player.group
        transparency = group.transparency
        ai_rec       = group.ai_recommendation
        rnd          = player.round_number

        round_explanation = ROUND_EXPLANATIONS.get(ai_rec, {}).get(rnd, '')

        score_rows = []
        for sup in SUPPLIERS:
            pa_sc = SUPPLIER_DATA[sup]['pa']
            pa_total = sum(pa_sc[c] * AI_WEIGHTS_PA[c] for c in AI_WEIGHTS_PA)
            score_rows.append({
                'supplier':   sup,
                'cost':       pa_sc['cost'],
                'delivery':   pa_sc['delivery'],
                'innovation': pa_sc['innovation'],
                'pa_total':   round(pa_total, 3),
            })

        return {
            'transparency':       transparency,
            'ai_recommendation':  ai_rec,
            'round_explanation':  round_explanation,
            'score_rows':         score_rows,
            'ai_weights_pa':      AI_WEIGHTS_PA,
            'is_high':            transparency == 'high',
            'round_number':       rnd,
            'ai_position':        group.ai_position,
            'is_middle':          group.ai_position == 'middle',
            'pa_initial_choice':  group.pa_initial_choice,  # shown in middle condition
        }


class SADecision(Page):
    """
    ASYNC: SA accesses this page independently after receiving notification that PA has submitted.
    SA sees PA's choice + their own CSR score table.
    AI recommendation is intentionally NOT passed — sequential AI→PA→SA structure.
    """
    @staticmethod
    def is_displayed(player): return is_sa(player)

    form_model  = 'group'
    form_fields = ['sa_choice']

    @staticmethod
    def vars_for_template(player):
        group        = player.group
        transparency = group.transparency

        score_rows = []
        for sup in SUPPLIERS:
            sa_sc = SUPPLIER_DATA[sup]['sa']
            sa_total = sum(sa_sc[c] * AI_WEIGHTS_SA[c] for c in AI_WEIGHTS_SA)
            score_rows.append({
                'supplier':    sup,
                'human_rights':sa_sc['human_rights'],
                'local':       sa_sc['local'],
                'carbon':      sa_sc['carbon'],
                'sa_total':    round(sa_total, 3),
            })

        return {
            'transparency':  transparency,
            'pa_choice':     group.pa_choice,
            'score_rows':    score_rows,
            'ai_weights_sa': AI_WEIGHTS_SA,
            'is_high':       transparency == 'high',
            'round_number':  player.round_number,
        }

    @staticmethod
    def before_next_page(player, timeout_happened):
        if not is_sa(player):
            return

        group = player.group
        group.set_performance()

        ai = group.ai_recommendation
        pa = group.pa_choice
        sa = group.sa_choice

        group.congruence_ai_pa = 'agree' if ai == pa else 'disagree'
        group.congruence_ai_sa = 'agree' if ai == sa else 'disagree'
        group.congruence_pa_sa = 'agree' if pa == sa else 'disagree'

        if ai == pa == sa:
            group.congruence_all = 'full'
        elif ai == sa or ai == pa or pa == sa:
            group.congruence_all = 'partial'
        else:
            group.congruence_all = 'none'


class RoundFeedback(Page):
    """
    Shown after each round (rounds 1–4).
    UPDATED: Δw explanation text now passed as template variable.
    Both PA and SA see this page — no wait page required in async structure.
    Note: in async mode, PA and SA may view this at different times.
    """
    @staticmethod
    def is_displayed(player): return is_not_last_round(player)

    @staticmethod
    def vars_for_template(player):
        group = player.group
        return {
            'round_number':      player.round_number,
            'next_round_number': player.round_number + 1,
            'ai_recommendation': group.ai_recommendation,
            'pa_choice':         group.pa_choice,
            'sa_choice':         group.sa_choice,
            'dw_pa':             group.dw_pa,
            'dw_sa':             group.dw_sa,
            'dominant_pa':       group.dominant_criterion_pa,
            'dominant_sa':       group.dominant_criterion_sa,
            'feedback_text':     group.ai_feedback_text,
            'feedback_paragraphs': [p for p in group.ai_feedback_text.split('\n\n') if p.strip()],
            'transparency':      group.transparency,
            'is_high':           group.transparency == 'high',
            'congruence_all':    group.congruence_all,
            'congruence_ai_pa':  group.congruence_ai_pa,
            'congruence_ai_sa':  group.congruence_ai_sa,
            'congruence_pa_sa':  group.congruence_pa_sa,
            'round_bonus':       group.round_bonus,
            'max_bonus':         MAX_BONUS_PER_ROUND,
            # Δw explanation — replaces need for participants to infer meaning
            'dw_explanation':    C.DW_EXPLANATION,
        }


class TrustSurvey(Page):
    """
    Post-experiment trust survey (Round 5 only).
    UPDATED: SA-specific intro text acknowledges SA did not interact with AI directly.
    McKnight items (reliability/functionality/helpfulness) unchanged — 7-pt, no N/A.
    Exploratory items (team/interpersonal/mc_transparency) include N/A (value=0).
    """
    @staticmethod
    def is_displayed(player): return is_last_round(player)

    form_model  = 'player'
    form_fields = [
        'trust_reliability_1', 'trust_reliability_2',
        'trust_reliability_3', 'trust_reliability_4',
        'trust_functionality_1', 'trust_functionality_2', 'trust_functionality_3',
        'trust_helpfulness_1',  'trust_helpfulness_2',
        'trust_helpfulness_3',  'trust_helpfulness_4',
        'trust_team_1', 'trust_team_2',
        'trust_interpersonal_1', 'trust_interpersonal_2',
        'mc_transparency_1', 'mc_transparency_2',
    ]

    @staticmethod
    def vars_for_template(player):
        # SA-specific intro acknowledges indirect AI exposure
        if is_sa(player):
            survey_intro = (
                "As the Sustainability Analyst, you did not interact with the AI system directly. "
                "Please answer the following questions based on your impression of how AI "
                "influenced the overall team process and your partner's decisions."
            )
        else:
            survey_intro = (
                "Please answer the following questions based on your experience "
                "with the AI system during the five rounds."
            )

        return {
            'scale_7':       list(range(1, 8)),
            'scale_5':       list(range(1, 6)),
            # N/A choices for exploratory items: 0 = "I could not assess this"
            'scale_7_na':    [0] + list(range(1, 8)),
            'scale_5_na':    [0] + list(range(1, 6)),
            'survey_intro':  survey_intro,
            'is_sa':         is_sa(player),
            # Reminder: similar-looking questions measure different dimensions
            'scale_note': (
                "Note: some questions may appear similar. Each item measures "
                "a distinct aspect of trust. Please respond to each one separately."
            ),
        }


class Demographics(Page):
    @staticmethod
    def is_displayed(player): return is_last_round(player)

    form_model  = 'player'
    form_fields = ['age', 'gender']


class Results(Page):
    @staticmethod
    def is_displayed(player): return is_last_round(player)

    @staticmethod
    def before_next_page(player, timeout_happened):
        """
        Distance-based payoff: sum of per-round bonuses across all 5 rounds.
        Max = 5 × €0.20 = €1.00
        """
        if is_last_round(player):
            total_bonus = sum(
                p.group.round_bonus for p in player.in_all_rounds()
            )
            player.payoff = round(total_bonus, 2)

    @staticmethod
    def vars_for_template(player):
        all_rounds = player.in_all_rounds()

        cumulative_dw_pa = round(sum(p.group.dw_pa for p in all_rounds), 4)
        cumulative_dw_sa = round(sum(p.group.dw_sa for p in all_rounds), 4)
        total_bonus      = round(sum(p.group.round_bonus for p in all_rounds), 2)

        round_summary = [
            {
                'round':       p.round_number,
                'ai_rec':      p.group.ai_recommendation,
                'pa_choice':   p.group.pa_choice,
                'sa_choice':   p.group.sa_choice,
                'dw_pa':       p.group.dw_pa,
                'dw_sa':       p.group.dw_sa,
                'dom_pa':      p.group.dominant_criterion_pa,
                'dom_sa':      p.group.dominant_criterion_sa,
                'congruence':  p.group.congruence_all,
                'round_bonus': p.group.round_bonus,
                'optimal':     p.group.sa_choice == OPTIMAL_SUPPLIER,
            }
            for p in all_rounds
        ]

        return {
            'cumulative_dw_pa':  cumulative_dw_pa,
            'cumulative_dw_sa':  cumulative_dw_sa,
            'round_summary':     round_summary,
            'transparency':      player.group.transparency,
            'total_bonus':       total_bonus,
            'max_total_bonus':   round(MAX_BONUS_PER_ROUND * C.NUM_ROUNDS, 2),
            'bonus_per_round':   MAX_BONUS_PER_ROUND,
            'dw_max':            DW_MAX,
        }


# ─────────────────────────────────────────────
# 8. PAGE SEQUENCE
# ─────────────────────────────────────────────
#
# ASYNC STRUCTURE — WaitPages removed:
#   BriefingWaitPage    → removed (PA and SA read Briefing independently)
#   SAWaitForPA         → removed (SA accesses SADecision after notification)
#   PAWaitForSA         → removed (PA proceeds to RoundFeedback independently)
#   RoundIntroWaitPage  → removed
#
# Notification mechanism (PA→SA handoff) must be handled externally:
#   Option A: Email trigger when PA submits AIRecommendation page
#   Option B: Shared dashboard where SA sees PA's submission status
#   Option C: Researcher monitors admin panel and sends SA link manually
#
# oTree admin panel: monitor session to confirm both players have completed
# each round before advancing to the next session-level step.

# ─────────────────────────────────────────────
# 8. PAGE SEQUENCE
# ─────────────────────────────────────────────
#
# All condition branches are in a single sequence.
# is_displayed() controls what each participant sees.
#
# SYNC / ASYNC (controlled by settings 'sync': True|False):
#   sync=True  → BriefingWaitPage, SAWaitForPA, PAWaitForSA, RoundIntroWaitPage shown
#   sync=False → those WaitPages return is_displayed=False → effectively skipped
#
# AI POSITION (controlled by settings 'ai_position': 'first'|'middle'):
#   'first'  → PAInitialDecision skipped (is_displayed=False)
#              sequence: AI → PA(choice) → SA
#   'middle' → PAInitialDecision shown to PA before AIRecommendation
#              sequence: PA(initial) → AI → PA(revised choice) → SA
#
# ACCURACY MODE (controlled by settings 'accuracy_mode': 'fixed'|'manipulation'):
#   'fixed'       → ai_recommendation redrawn each round in creating_session
#   'manipulation'→ ai_recommendation fixed for all rounds from Round 1
#   (no page-level change — handled entirely in creating_session)
#
# ACTIVE SETTINGS COMBINATIONS:
#   Lab  / first  / fixed        → sync=True,  ai_position='first',  accuracy_mode='fixed'
#   Lab  / middle / fixed        → sync=True,  ai_position='middle', accuracy_mode='fixed'
#   Lab  / first  / manipulation → sync=True,  ai_position='first',  accuracy_mode='manipulation'
#   Lab  / middle / manipulation → sync=True,  ai_position='middle', accuracy_mode='manipulation'
#   Online/first  / fixed        → sync=False, ai_position='first',  accuracy_mode='fixed'
#   Online/middle / fixed        → sync=False, ai_position='middle', accuracy_mode='fixed'
#   Online/first  / manipulation → sync=False, ai_position='first',  accuracy_mode='manipulation'
#   Online/middle / manipulation → sync=False, ai_position='middle', accuracy_mode='manipulation'

page_sequence = [
    Consent,
    BaselineTrust,          # Round 1 only
    RoleAssignment,
    Briefing,
    ComprehensionCheck,     # Round 1 only, recording mode
    BriefingWaitPage,       # sync=True + Round 1 only
    RoundIntro,             # Rounds 2-5, shows previous round summary
    RoundIntroWaitPage,     # sync=True + Rounds 2-5 only
    PAInitialDecision,      # PA only + ai_position='middle' only
    SAWaitForPAInitial,     # SA only + sync=True + ai_position='middle' only
    AIRecommendation,       # PA only (sees AI + submits final choice)
    SAWaitForPA,            # SA only + sync=True (waits after PA submits)
    SADecision,             # SA only
    PAWaitForSA,            # PA only + sync=True only
    RoundFeedback,          # Rounds 1-4 only
    TrustSurvey,            # Round 5 only
    Demographics,           # Round 5 only
    Results,                # Round 5 only
]
