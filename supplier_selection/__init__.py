"""
Trust in Human-AI Teams in B2B Supplier Selection
oTree Experiment — __init__.py  (v6 — Option A: role-allocation redesign)

Changes from v5:
  - ai_position ('first'/'middle') RETIRED. Replaced by augmented_role
    ('principal'/'agent'), which controls WHICH team role is exposed to AI,
    not WHEN within one role's own judgment process.
  - Role order REVERSED: Sustainability Analyst (SA) now decides FIRST in
    every condition (principal-agent framing: SA = principal, PA = agent).
    Purchasing Analyst (PA) decides SECOND and renders the team's binding
    final choice — a reversal from v5, where PA went first and SA was final.
  - augmented_role='principal' → SA reviews AI's recommendation (transparency
    applies here) + CSR criteria, decides; PA then reviews SA's decision +
    purchasing criteria, with NO AI, and renders the final choice.
  - augmented_role='agent'     → SA submits an independent CSR-only decision,
    no AI; PA then reviews SA's decision + purchasing criteria + AI's
    recommendation (transparency applies here), and renders the final choice.
  - BLINDING: the non-augmented partner is never told the other's decision
    involved AI. Full disclosure happens only in the Results-page debrief.
  - has_ai=False (human control): SA decides first (CSR-only, no AI), PA
    decides second (purchasing + SA's choice, no AI) — same role order as
    the AI conditions, just with no AI anywhere.
  - Per-round Δw is no longer shown as a raw number (only a qualitative
    read + the round's money bonus). Exact Δw is revealed only once, in
    the Results-page summary at the end of round 5.
  - SYNC / ASYNC controlled via settings.py 'sync': True | False
  - ACCURACY MODE controlled via settings.py 'accuracy_mode': 'fixed' | 'manipulation'
      fixed        → draw once per round (true 70% average, not manipulated)
      manipulation → draw once per session (session fixed: always A or always E)
"""

import random
from otree.api import (
    BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Page, WaitPage, models, widgets, Currency,
)

# ─────────────────────────────────────────────
# 1. CONSTANTS & SUPPLIER DATA
# ─────────────────────────────────────────────

# Fictional company used only for narrative framing (Briefing scenario).
# Not a real company — invented for the experiment's cover story.
SCENARIO_COMPANY = 'Auroria Energy'

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

DW_PA_MAX = round(
    sum(abs(SUPPLIER_DATA[OPTIMAL_SUPPLIER]['pa'][c] - SUPPLIER_DATA['E']['pa'][c]) * w
        for c, w in AI_WEIGHTS_PA.items()), 4)

DW_SA_MAX = round(
    sum(abs(SUPPLIER_DATA[OPTIMAL_SUPPLIER]['sa'][c] - SUPPLIER_DATA['E']['sa'][c]) * w
        for c, w in AI_WEIGHTS_SA.items()), 4)

DW_MAX = round((DW_PA_MAX + DW_SA_MAX) / 2, 4)

MAX_BONUS_PER_ROUND = 1.00  # 5 rounds x 1.00 = max €5 bonus, on top of €10 fixed fee (total ceiling €15)


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
    if random.random() < AI_ACCURACY:
        return OPTIMAL_SUPPLIER
    return ERROR_SUPPLIER


def compute_dw(team_choice: str, perspective: str) -> tuple:
    weights = AI_WEIGHTS_PA if perspective == 'pa' else AI_WEIGHTS_SA
    opt_sc  = SUPPLIER_DATA[OPTIMAL_SUPPLIER][perspective]
    team_sc = SUPPLIER_DATA[team_choice][perspective]

    gaps = {c: abs(opt_sc[c] - team_sc[c]) * w for c, w in weights.items()}
    dw   = sum(gaps.values())
    dom  = max(gaps, key=gaps.get) if dw > 0 else ''
    return round(dw, 4), dom


def compute_distance_bonus(dw_pa: float, dw_sa: float) -> float:
    if DW_MAX == 0:
        return MAX_BONUS_PER_ROUND
    combined_dw = (dw_pa + dw_sa) / 2
    bonus = MAX_BONUS_PER_ROUND * (1 - combined_dw / DW_MAX)
    return round(max(0.0, min(MAX_BONUS_PER_ROUND, bonus)), 4)


def qualitative_gap(dw: float) -> str:
    """Coarse, non-numeric read of a Δw gap for per-round display. Exact
    figures are reserved for the Results-page summary at the end of round 5
    (see Decision Log / Voice 127: revealing exact Δw every round let sharp
    participants realize they had 'solved' the task and stop reconsidering)."""
    if dw <= 0:
        return "right on target"
    if dw < DW_MAX * 0.2:
        return "very close to optimal"
    if dw < DW_MAX * 0.5:
        return "a moderate gap from optimal"
    return "a notable gap from optimal"


def build_feedback_text(
    ai_recommendation: str,
    team_choice: str,
    transparency: str,
    dw_pa: float, dom_pa: str,
    dw_sa: float, dom_sa: str,
) -> str:
    level = 'high' if transparency == 'high' else 'low'

    if ai_recommendation == OPTIMAL_SUPPLIER:
        pa_text = PA_FEEDBACK_AI_A.get(team_choice, PA_FEEDBACK_AI_A['A'])[level]
        sa_text = SA_FEEDBACK_AI_A.get(team_choice, SA_FEEDBACK_AI_A['A'])[level]
    else:
        pa_lut  = PA_FEEDBACK_AI_E.get(team_choice, PA_FEEDBACK_AI_E['default'])
        sa_lut  = SA_FEEDBACK_AI_E.get(team_choice, SA_FEEDBACK_AI_E['default'])
        pa_text = pa_lut[level]
        sa_text = sa_lut[level]

    if transparency == 'high':
        pa_block = (
            f"[Purchasing Criteria]\n{pa_text}\n"
            f"Your team's choice was {qualitative_gap(dw_pa)}"
            f"{' — dominant gap: ' + dom_pa if dom_pa else ''}."
        )
        sa_block = (
            f"[CSR Criteria]\n{sa_text}\n"
            f"Your team's choice was {qualitative_gap(dw_sa)}"
            f"{' — dominant gap: ' + dom_sa if dom_sa else ''}."
        )
        return "\n\n".join([pa_block, sa_block])
    return f"{pa_text}\n\n{sa_text}"


def build_feedback_text_control(
    team_choice: str,
    transparency: str,
    dw_pa: float, dom_pa: str,
    dw_sa: float, dom_sa: str,
) -> str:
    """
    HUMAN CONTROL condition feedback — reports the team's own performance
    gap against the optimal supplier, with no reference to an AI at all
    (there is none in this condition).
    """
    if transparency == 'high':
        pa_block = (
            f"[Purchasing Criteria]\nYour team selected Supplier {team_choice}. "
            f"That choice was {qualitative_gap(dw_pa)}"
            f"{' — dominant gap: ' + dom_pa if dom_pa else ''}."
        )
        sa_block = (
            f"[CSR Criteria]\nThat choice was {qualitative_gap(dw_sa)}"
            f"{' — dominant gap: ' + dom_sa if dom_sa else ''}."
        )
        return "\n\n".join([pa_block, sa_block])

    if dw_pa == 0 and dw_sa == 0:
        return (
            "Your team's choice matched the optimal supplier on both "
            "purchasing and CSR criteria this round."
        )
    return (
        "Your team's choice diverged from the optimal supplier on one or "
        "more criteria this round."
    )


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

    DW_EXPLANATION = (
        "This score shows how far the team's final choice is from the theoretically "
        "optimal supplier — not how much the Purchasing Analyst and Sustainability "
        "Analyst disagreed. A lower score means the team's decision was closer to "
        "the best possible outcome."
    )

    ROUND_REPEAT_RATIONALE = (
        "You will go through 5 rounds using the same suppliers and criteria "
        "each time. Please give your best judgment independently in each "
        "round, based on the information available to you at that time."
    )


class Subsession(BaseSubsession):
    pass


# 🔧 ROOT CAUSE FIX — oTree's session-builder looks up 'creating_session' as a
# MODULE-LEVEL function (no-self style: getattr(module, 'creating_session', None)),
# NOT as a method inside class Subsession. Defined as a class method, oTree's
# getattr() just returns None and silently skips calling it — no error, no crash,
# which is exactly why the earlier raise-RuntimeError test never fired.
# Fix: define it at module level, taking `subsession` as the first argument.
def creating_session(subsession):
    has_ai = subsession.session.config.get('has_ai', True)

    if not has_ai:
        # HUMAN CONTROL condition: no AI recommendation is drawn or shown at
        # all. group.transparency / augmented_role / ai_recommendation stay
        # blank — unused by any page when has_ai=False.
        return

    transparency   = subsession.session.config.get('transparency',   'high')
    augmented_role = subsession.session.config.get('augmented_role', 'principal')
    accuracy_mode  = subsession.session.config.get('accuracy_mode',  'fixed')

    if accuracy_mode == 'manipulation':
        if subsession.round_number == 1:
            ai_rec = get_ai_recommendation(accuracy_mode)
            subsession.session.vars['ai_recommendation'] = ai_rec
        else:
            ai_rec = subsession.session.vars.get('ai_recommendation', OPTIMAL_SUPPLIER)
    else:
        ai_rec = get_ai_recommendation(accuracy_mode)
        subsession.session.vars['ai_recommendation'] = ai_rec

    for group in subsession.get_groups():
        group.transparency      = transparency
        group.augmented_role    = augmented_role
        group.ai_recommendation = ai_rec


class Group(BaseGroup):
    transparency      = models.StringField(initial='')
    # 'principal' (SA is AI-augmented) or 'agent' (PA is AI-augmented).
    # Blank when has_ai=False (human control — neither role sees AI).
    augmented_role    = models.StringField(initial='')
    ai_recommendation = models.StringField(initial='')

    # SA decides FIRST in every condition (principal-agent framing: SA is the
    # principal issuing an initial, CSR-informed recommendation).
    sa_choice = models.StringField(
        choices=SUPPLIERS,
        label="Based on the CSR criteria, which supplier do you recommend to the Purchasing Analyst?"
    )
    # PA decides SECOND and renders the team's binding final choice (the
    # agent who executes/finalizes, informed by the SA's prior decision).
    pa_choice = models.StringField(
        choices=SUPPLIERS,
        label="Considering your partner's recommendation and the purchasing criteria, which supplier does the team select?"
    )

    dw_pa                 = models.FloatField(initial=0.0)
    dw_sa                 = models.FloatField(initial=0.0)
    dominant_criterion_pa = models.StringField(initial='')
    dominant_criterion_sa = models.StringField(initial='')

    # SA's OWN first-phase choice scored under her own CSR criteria — a
    # genuine solo/pre-partner-input judgment quality measure, independent
    # of whatever the team's eventual final choice (pa_choice) turns out to
    # be. Useful for complementarity analyses (Paper 4) that need a solo
    # baseline distinct from the team's final decision.
    dw_sa_initial                 = models.FloatField(initial=0.0)
    dominant_criterion_sa_initial = models.StringField(initial='')

    congruence_ai_pa = models.StringField(initial='')
    congruence_ai_sa = models.StringField(initial='')
    congruence_pa_sa = models.StringField(initial='')
    congruence_all   = models.StringField(initial='')
    # Whether the AI's recommendation matched the choice of whichever role
    # actually saw it this session (SA if principal-augmented, PA if
    # agent-augmented) — the most direct advice-taking measure, independent
    # of which role that happens to be. Blank when has_ai=False.
    congruence_ai_augmented = models.StringField(initial='')

    ai_feedback_text  = models.LongStringField(initial='')
    round_bonus       = models.FloatField(initial=0.0)

    def set_performance(self):
        # The TEAM's binding final choice is now the PA's decision (PA acts
        # second, informed by the SA's prior choice) — a reversal from the
        # pre-Option-A design, where the SA's choice was the team's final one.
        team_choice = self.pa_choice

        dw_pa, dom_pa = compute_dw(team_choice, 'pa')
        self.dw_pa                 = dw_pa
        self.dominant_criterion_pa = dom_pa

        dw_sa, dom_sa = compute_dw(team_choice, 'sa')
        self.dw_sa                 = dw_sa
        self.dominant_criterion_sa = dom_sa

        # SA's own solo judgment quality, evaluated on her own first-phase
        # choice (sa_choice) rather than the team's eventual final choice.
        dw_sa_init, dom_sa_init          = compute_dw(self.sa_choice, 'sa')
        self.dw_sa_initial               = dw_sa_init
        self.dominant_criterion_sa_initial = dom_sa_init

        self.round_bonus = compute_distance_bonus(dw_pa, dw_sa)

        # 🛡️ 안전장치: group.transparency가 비어있으면 session config에서 가져옴
        transparency_val = self.transparency or self.session.config.get('transparency', 'low')

        if self.session.config.get('has_ai', True):
            self.ai_feedback_text = build_feedback_text(
                ai_recommendation=self.ai_recommendation,
                team_choice=team_choice,
                transparency=transparency_val,
                dw_pa=dw_pa, dom_pa=dom_pa,
                dw_sa=dw_sa, dom_sa=dom_sa,
            )
        else:
            self.ai_feedback_text = build_feedback_text_control(
                team_choice=team_choice,
                transparency=transparency_val,
                dw_pa=dw_pa, dom_pa=dom_pa,
                dw_sa=dw_sa, dom_sa=dom_sa,
            )


class Player(BasePlayer):
    role_label = models.StringField()

    consent_given = models.BooleanField(
        label=(
            "I have read and understood the consent form above. "
            "I agree to participate voluntarily. / "
            "J'ai lu et compris le formulaire de consentement ci-dessus. "
            "J'accepte de participer volontairement."
        ),
        widget=widgets.CheckboxInput,
    )

    # Separate, independent consent item (official consent form Section 5/6):
    # future reuse of anonymised data is NOT a condition of participation —
    # participants must explicitly choose one option, with no pre-selected default.
    consent_future_reuse = models.BooleanField(
        choices=[
            [True, (
                "I agree that my anonymised data may be reused in subsequent "
                "studies within the same research program. / "
                "J'accepte que mes données anonymisées soient réutilisées dans "
                "le cadre d'études ultérieures relevant du même programme de recherche."
            )],
            [False, (
                "I do not agree that my anonymised data may be reused beyond "
                "this project. / "
                "Je n'accepte pas que mes données anonymisées soient réutilisées "
                "au-delà du présent projet."
            )],
        ],
        widget=widgets.RadioSelect,
        label="",
    )

    baseline_ai_trust_1 = models.IntegerField(
        label="In general, I trust AI-based recommendation systems to provide accurate information.",
        choices=list(range(1, 8)), widget=widgets.RadioSelect)
    baseline_ai_trust_2 = models.IntegerField(
        label="I believe AI systems can make reliable decisions in business contexts.",
        choices=list(range(1, 8)), widget=widgets.RadioSelect)
    baseline_ai_trust_3 = models.IntegerField(
        label="I am comfortable relying on AI tools when making important decisions.",
        choices=list(range(1, 8)), widget=widgets.RadioSelect)

    baseline_domain_procurement = models.IntegerField(
        label="How familiar are you with B2B procurement processes?",
        choices=list(range(1, 8)), widget=widgets.RadioSelect)
    baseline_domain_esg = models.IntegerField(
        label="How familiar are you with ESG/CSR criteria in supplier evaluation?",
        choices=list(range(1, 8)), widget=widgets.RadioSelect)

    baseline_ai_frequency = models.IntegerField(
        label="How often do you use AI tools in your work or studies?",
        choices=list(range(1, 8)), widget=widgets.RadioSelect)
    baseline_ai_decision = models.StringField(
        label="Have you previously used AI for decision-making support?",
        choices=[['yes', 'Yes'], ['no', 'No']],
        widget=widgets.RadioSelect)

    trust_reliability_1 = models.IntegerField(
        label="The AI system is a very reliable source of recommendations.",
        choices=list(range(1, 8)), widget=widgets.RadioSelect)
    trust_reliability_2 = models.IntegerField(
        label="The AI system does not fail me.",
        choices=list(range(1, 8)), widget=widgets.RadioSelect)
    trust_reliability_3 = models.IntegerField(
        label="The AI system is extremely dependable.",
        choices=list(range(1, 8)), widget=widgets.RadioSelect)
    trust_reliability_4 = models.IntegerField(
        label="The AI system does not malfunction for me.",
        choices=list(range(1, 8)), widget=widgets.RadioSelect)

    trust_functionality_1 = models.IntegerField(
        label="The AI system has the functionality I need.",
        choices=list(range(1, 8)), widget=widgets.RadioSelect)
    trust_functionality_2 = models.IntegerField(
        label="The AI system has the features required for this task.",
        choices=list(range(1, 8)), widget=widgets.RadioSelect)
    trust_functionality_3 = models.IntegerField(
        label="The AI system has the ability to do what I want it to do.",
        choices=list(range(1, 8)), widget=widgets.RadioSelect)

    trust_helpfulness_1 = models.IntegerField(
        label="The AI system supplies the help I need through its recommendations.",
        choices=list(range(1, 8)), widget=widgets.RadioSelect)
    trust_helpfulness_2 = models.IntegerField(
        label="The AI system provides competent guidance through its recommendations.",
        choices=list(range(1, 8)), widget=widgets.RadioSelect)
    trust_helpfulness_3 = models.IntegerField(
        label="The AI system provides whatever help I need.",
        choices=list(range(1, 8)), widget=widgets.RadioSelect)
    trust_helpfulness_4 = models.IntegerField(
        label="The AI system provides very sensible and effective advice.",
        choices=list(range(1, 8)), widget=widgets.RadioSelect)

    trust_team_1 = models.IntegerField(
        label="Overall, I trust this team.",
        choices=[0, 1, 2, 3, 4, 5, 6, 7],
        widget=widgets.RadioSelect)
    trust_team_2 = models.IntegerField(
        label="I am satisfied with the team decision-making process involving the AI.",
        choices=[0, 1, 2, 3, 4, 5, 6, 7],
        widget=widgets.RadioSelect)

    trust_interpersonal_1 = models.IntegerField(
        label="My human team member is very capable of performing their job.",
        choices=[0, 1, 2, 3, 4, 5, 6, 7],
        widget=widgets.RadioSelect)
    trust_interpersonal_2 = models.IntegerField(
        label="I trust my team partner's judgment in this task.",
        choices=[0, 1, 2, 3, 4, 5, 6, 7],
        widget=widgets.RadioSelect)

    mc_transparency_1 = models.IntegerField(
        label="The AI system provided a clear explanation of how it reached its recommendation.",
        choices=[0, 1, 2, 3, 4, 5, 6, 7],
        widget=widgets.RadioSelect)
    mc_transparency_2 = models.IntegerField(
        label="I could understand the criteria and weights used by the AI.",
        choices=[0, 1, 2, 3, 4, 5, 6, 7],
        widget=widgets.RadioSelect)

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
    comprehension_score = models.IntegerField(initial=0)

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
    form_fields = ['consent_given', 'consent_future_reuse']

    @staticmethod
    def error_message(player, values):
        if not values.get('consent_given'):
            return (
                'You must agree to the consent form to participate. / '
                'Vous devez accepter le formulaire de consentement pour participer.'
            )
        # Note: consent_future_reuse is a separate, independent choice —
        # both True and False are valid answers; only a missing answer is an error,
        # which oTree already enforces automatically for a required field with no default.


class BaselineTrust(Page):
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
    @staticmethod
    def is_displayed(player): return is_round_1(player)

    form_model  = 'player'
    form_fields = ['comprehension_q1', 'comprehension_q2']

    @staticmethod
    def before_next_page(player, timeout_happened):
        correct = {
            'comprehension_q1': 'b',  # PA renders the team's final choice (Option A)
            'comprehension_q2': 'b',
        }
        score = sum(
            1 for field, answer in correct.items()
            if getattr(player, field) == answer
        )
        player.comprehension_score = score

    @staticmethod
    def vars_for_template(player):
        return {'round_number': player.round_number}


class RoleAssignment(Page):
    @staticmethod
    def is_displayed(player): return is_round_1(player)

    @staticmethod
    def vars_for_template(player):
        role = C.ROLE_PA if is_pa(player) else C.ROLE_SA
        player.role_label = role
        return {
            'role':            role,
            'is_pa':           is_pa(player),
            'has_ai':          has_ai(player),
            'was_augmented':   was_augmented(player),
        }


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
            'is_pa':                  is_pa(player),
            'has_ai':                 has_ai(player),
            'is_principal_augmented': is_augmented_principal(player),
            'is_agent_augmented':     is_augmented_agent(player),
            'company_name':           SCENARIO_COMPANY,
            'pa_rows':                pa_rows,
            'sa_rows':                sa_rows,
            'ai_weights_pa':          AI_WEIGHTS_PA,
            'ai_weights_sa':          AI_WEIGHTS_SA,
            'round_repeat_rationale': C.ROUND_REPEAT_RATIONALE,
        }


class RoundIntro(Page):
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
                'sa_choice':    prev_group.sa_choice,
                'pa_choice':    prev_group.pa_choice,
                'congruence':   prev_group.congruence_all,
                'round_bonus':  prev_group.round_bonus,
                'optimal':      prev_group.pa_choice == OPTIMAL_SUPPLIER,
            }

        return {
            'round_number':    player.round_number,
            'prev_round_data': prev_round_data,
            'is_pa':           is_pa(player),
            'has_ai':          has_ai(player),
            'is_principal_augmented': is_augmented_principal(player),
            'is_agent_augmented':     is_augmented_agent(player),
        }


def is_sync(player):
    return player.session.config.get('sync', True)

def is_async(player):
    return not player.session.config.get('sync', True)

def has_ai(player):
    return player.session.config.get('has_ai', True)

def augmented_role(player):
    """'principal' | 'agent' | '' (blank when has_ai=False)."""
    return player.session.config.get('augmented_role', 'principal') if has_ai(player) else ''

def is_augmented_principal(player):
    return has_ai(player) and augmented_role(player) == 'principal'

def is_augmented_agent(player):
    return has_ai(player) and augmented_role(player) == 'agent'

def was_augmented(player):
    """True if THIS player's role was the one exposed to AI this session."""
    if not has_ai(player):
        return False
    role = augmented_role(player)
    return (role == 'principal' and is_sa(player)) or (role == 'agent' and is_pa(player))


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


class SADecision(Page):
    """
    SA decides FIRST in every condition (principal-agent framing: SA is the
    principal). When augmented_role='principal' (and has_ai), SA sees the
    AI's recommendation (transparency-conditional) alongside the CSR
    criteria. Otherwise (augmented_role='agent', or has_ai=False), SA
    decides independently from the CSR criteria alone — no AI shown.
    """
    @staticmethod
    def is_displayed(player): return is_sa(player)

    form_model  = 'group'
    form_fields = ['sa_choice']

    @staticmethod
    def vars_for_template(player):
        group        = player.group
        shows_ai     = is_augmented_principal(player)
        transparency = group.transparency or player.session.config.get('transparency', 'low')
        rnd          = player.round_number

        ai_rec = ''
        round_explanation = ''
        if shows_ai:
            ai_rec = group.ai_recommendation
            if not ai_rec:
                ai_rec = player.session.vars.get('ai_recommendation', 'A')
                group.ai_recommendation = ai_rec
            round_explanation = ROUND_EXPLANATIONS.get(ai_rec, {}).get(rnd, '')

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
            'shows_ai':          shows_ai,
            'transparency':      transparency,
            'ai_recommendation': ai_rec,
            'round_explanation': round_explanation,
            'score_rows':        score_rows,
            'ai_weights_sa':     AI_WEIGHTS_SA,
            'is_high':           transparency == 'high',
            'round_number':      rnd,
        }


class PAWaitForSA(WaitPage):
    @staticmethod
    def is_displayed(player):
        return is_pa(player) and is_sync(player)
    title_text = "Waiting for the Sustainability Analyst…"
    body_text  = "Your partner is reviewing the information and submitting an initial recommendation. Please wait."


class PADecision(Page):
    """
    PA decides SECOND in every condition and renders the team's binding
    final choice (the agent who executes/finalizes). PA always sees the
    SA's prior decision, framed simply as "your partner's recommendation"
    — never revealing whether that decision involved AI (blinding, see
    module docstring). When augmented_role='agent' (and has_ai), PA also
    sees the AI's own recommendation (transparency-conditional) alongside
    the purchasing criteria. Otherwise, PA decides from the purchasing
    criteria and the partner's choice alone — no AI shown.
    """
    @staticmethod
    def is_displayed(player): return is_pa(player)

    form_model  = 'group'
    form_fields = ['pa_choice']

    @staticmethod
    def vars_for_template(player):
        group        = player.group
        shows_ai     = is_augmented_agent(player)
        transparency = group.transparency or player.session.config.get('transparency', 'low')
        rnd          = player.round_number

        ai_rec = ''
        round_explanation = ''
        if shows_ai:
            ai_rec = group.ai_recommendation
            if not ai_rec:
                ai_rec = player.session.vars.get('ai_recommendation', 'A')
                group.ai_recommendation = ai_rec
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
            'shows_ai':          shows_ai,
            'transparency':      transparency,
            'ai_recommendation': ai_rec,
            'round_explanation': round_explanation,
            'score_rows':        score_rows,
            'ai_weights_pa':     AI_WEIGHTS_PA,
            'is_high':           transparency == 'high',
            'round_number':      rnd,
            'sa_choice':         group.sa_choice,
        }

    @staticmethod
    def before_next_page(player, timeout_happened):
        if not is_pa(player):
            return

        group = player.group
        group.set_performance()

        ai   = group.ai_recommendation
        sa   = group.sa_choice
        pa   = group.pa_choice
        role = group.augmented_role

        group.congruence_pa_sa = 'agree' if pa == sa else 'disagree'

        if has_ai(player):
            # The AI was only shown to whichever role is augmented this
            # session — compare it against that role's choice, not always PA.
            augmented_choice = sa if role == 'principal' else pa
            group.congruence_ai_augmented = 'agree' if ai == augmented_choice else 'disagree'
            group.congruence_ai_pa = 'agree' if ai == pa else 'disagree'
            group.congruence_ai_sa = 'agree' if ai == sa else 'disagree'
            if ai == pa == sa:
                group.congruence_all = 'full'
            elif ai == sa or ai == pa or pa == sa:
                group.congruence_all = 'partial'
            else:
                group.congruence_all = 'none'
        else:
            # HUMAN CONTROL: no AI vertex exists, so AI-congruence fields are
            # not applicable — left blank rather than misleadingly 'disagree'.
            group.congruence_ai_augmented = ''
            group.congruence_ai_pa = ''
            group.congruence_ai_sa = ''
            group.congruence_all  = group.congruence_pa_sa


class SAWaitForPA(WaitPage):
    @staticmethod
    def is_displayed(player):
        return is_sa(player) and is_sync(player)
    title_text = "Waiting for the Purchasing Analyst…"
    body_text  = "Your partner is reviewing your recommendation and making the team's final decision. Please wait."


class RoundFeedback(Page):
    @staticmethod
    def is_displayed(player): return is_not_last_round(player)

    @staticmethod
    def vars_for_template(player):
        group = player.group
        transparency_val = group.transparency or player.session.config.get('transparency', 'low')
        return {
            'round_number':      player.round_number,
            'next_round_number': player.round_number + 1,
            'has_ai':            has_ai(player),
            'ai_recommendation': group.ai_recommendation,
            'sa_choice':         group.sa_choice,
            'pa_choice':         group.pa_choice,
            'is_principal_augmented': is_augmented_principal(player),
            'is_agent_augmented':     is_augmented_agent(player),
            # No raw Δw here by design — exact figures are reserved for the
            # Results-page summary at the end of round 5 (Voice 127 decision).
            'feedback_text':     group.ai_feedback_text,
            'feedback_paragraphs': [p for p in group.ai_feedback_text.split('\n\n') if p.strip()],
            'transparency':      transparency_val,
            'is_high':           transparency_val == 'high',
            'congruence_all':    group.congruence_all,
            'congruence_ai_augmented': group.congruence_ai_augmented,
            'congruence_pa_sa':  group.congruence_pa_sa,
            'round_bonus':       group.round_bonus,
            'max_bonus':         MAX_BONUS_PER_ROUND,
        }


class TrustSurvey(Page):
    @staticmethod
    def is_displayed(player): return is_last_round(player)

    form_model  = 'player'

    @staticmethod
    def get_form_fields(player):
        # AI-directed trust items (reliability/functionality/helpfulness/
        # transparency) only make sense for whichever role actually saw the
        # AI this session (was_augmented) — NOT simply has_ai, since under
        # Option A one of the two roles never encounters the AI even when
        # has_ai=True. The non-augmented role (and both roles under the
        # human-control condition) keeps only the team/interpersonal items.
        team_fields = [
            'trust_team_1', 'trust_team_2',
            'trust_interpersonal_1', 'trust_interpersonal_2',
        ]
        if was_augmented(player):
            return [
                'trust_reliability_1', 'trust_reliability_2',
                'trust_reliability_3', 'trust_reliability_4',
                'trust_functionality_1', 'trust_functionality_2', 'trust_functionality_3',
                'trust_helpfulness_1',  'trust_helpfulness_2',
                'trust_helpfulness_3',  'trust_helpfulness_4',
            ] + team_fields + ['mc_transparency_1', 'mc_transparency_2']
        return team_fields

    @staticmethod
    def vars_for_template(player):
        if not has_ai(player):
            survey_intro = (
                "Please answer the following questions based on your experience "
                "working with your partner during the five rounds."
            )
        elif was_augmented(player):
            survey_intro = (
                "Please answer the following questions based on your experience "
                "with the AI system during the five rounds."
            )
        else:
            survey_intro = (
                "You did not interact with the AI system directly this session. "
                "Please answer the following questions based on your impression of how AI "
                "influenced the overall team process and your partner's decisions."
            )

        return {
            'scale_7':       list(range(1, 8)),
            'scale_7_na':    [0] + list(range(1, 8)),
            'survey_intro':  survey_intro,
            'was_augmented': was_augmented(player),
            'has_ai':        has_ai(player),
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
    def is_displayed(player): 
        return is_last_round(player)

    @staticmethod
    def vars_for_template(player):
        all_rounds = player.in_all_rounds()

        cumulative_dw_pa = round(sum((p.group.dw_pa or 0.0) for p in all_rounds), 4)
        cumulative_dw_sa = round(sum((p.group.dw_sa or 0.0) for p in all_rounds), 4)
        total_bonus      = round(sum((p.group.round_bonus or 0.0) for p in all_rounds), 2)

        player.payoff = total_bonus

        # The team's binding final choice is now the PA's decision (Option A:
        # PA acts second, informed by the SA's prior choice).
        optimal_rounds = sum(1 for p in all_rounds if p.group.pa_choice == OPTIMAL_SUPPLIER)

        # 🛡️ 안전장치: group.transparency가 비어있으면 session.config에서 가져옴
        transparency_val = player.group.transparency or player.session.config.get('transparency', 'low')

        # Debrief text branches by the accuracy_mode actually experienced by
        # this participant's session, so the debrief accurately reflects
        # what they went through rather than a one-size-fits-all statement.
        # For the human control condition (has_ai=False), no AI accuracy
        # mechanism applies at all, so this text is left blank and the
        # template shows a control-specific debrief paragraph instead.
        if not has_ai(player):
            debrief_accuracy_text = ''
        else:
            accuracy_mode_val = player.session.config.get('accuracy_mode', 'fixed')
            if accuracy_mode_val == 'manipulation':
                debrief_accuracy_text = (
                    "In your session specifically, the AI's accuracy was set once at "
                    "the very start and held constant for all 5 rounds — so you "
                    "experienced either a consistently accurate AI, or a consistently "
                    "inaccurate one, for your entire session."
                )
            else:
                debrief_accuracy_text = (
                    "In your session specifically, the AI's accuracy was re-drawn "
                    "independently each round (correct about 70% of the time on "
                    "average) — so its reliability could vary from round to round."
                )

        # Blinding disclosure: during the task, the non-augmented partner was
        # never told the other's decision involved AI (see module docstring).
        # The approved consent protocol promises full disclosure in this
        # debrief, so the non-augmented role learns it here for the first time.
        debrief_blinding_text = ''
        if has_ai(player) and not was_augmented(player):
            if augmented_role(player) == 'principal':
                debrief_blinding_text = (
                    "One thing we did not tell you during the task: your partner's "
                    "initial recommendation (as Sustainability Analyst) was made with "
                    "the help of the AI system's recommendation. You were only shown "
                    "your partner's resulting recommendation, not that the AI was involved."
                )
            else:
                debrief_blinding_text = (
                    "One thing we did not tell you during the task: your partner's "
                    "final decision (as Purchasing Analyst) was made with the help of "
                    "the AI system's recommendation, in addition to your own "
                    "recommendation. You were not told that the AI was involved."
                )

        round_summary = []
        for p in all_rounds:
            g = p.group
            pa_choice = g.pa_choice or ''
            round_summary.append({
                'round':       p.round_number,
                'ai_rec':      g.ai_recommendation or '',
                'sa_choice':   g.sa_choice or '',
                'pa_choice':   pa_choice,
                'dw_pa':       g.dw_pa or 0.0,
                'dw_sa':       g.dw_sa or 0.0,
                'dom_pa':      g.dominant_criterion_pa or '',
                'dom_sa':      g.dominant_criterion_sa or '',
                'congruence':  g.congruence_all or '',
                'round_bonus': g.round_bonus or 0.0,
                'optimal':     pa_choice == OPTIMAL_SUPPLIER if pa_choice else False,
            })

        return {
            'transparency':       transparency_val,
            'optimal_rounds':     optimal_rounds,
            'bonus_per_round':   MAX_BONUS_PER_ROUND,
            'performance_bonus': total_bonus,
            'cumulative_dw_pa':  cumulative_dw_pa,
            'cumulative_dw_sa':  cumulative_dw_sa,
            'round_summary':     round_summary,
            'has_ai':            has_ai(player),
            'debrief_accuracy_text': debrief_accuracy_text,
            'debrief_blinding_text': debrief_blinding_text,
            'contact_email':     'jian.lee03@kedgebs.com',
        }

# ─────────────────────────────────────────────
# 8. PAGE SEQUENCE
# ─────────────────────────────────────────────

page_sequence = [
    Consent,
    BaselineTrust,          # Round 1 only
    RoleAssignment,
    Briefing,
    ComprehensionCheck,     # Round 1 only, recording mode
    BriefingWaitPage,       # sync=True + Round 1 only
    RoundIntro,             # Rounds 2-5, shows previous round summary
    RoundIntroWaitPage,     # sync=True + Rounds 2-5 only
    SADecision,             # SA only — decides FIRST (with AI if principal-augmented, else solo)
    PAWaitForSA,            # PA only + sync=True (waits while SA decides)
    PADecision,             # PA only — decides SECOND, renders team's final choice
                            #   (with AI if agent-augmented, else sees only SA's choice)
    SAWaitForPA,            # SA only + sync=True (waits while PA finalizes)
    RoundFeedback,          # Rounds 1-4 only
    TrustSurvey,            # Round 5 only
    Demographics,           # Round 5 only
    Results,                # Round 5 only
]