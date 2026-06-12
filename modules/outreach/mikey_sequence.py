"""

Mikey / Gaurav cold email — blueprint-aligned service pitch.



WEBSITE  → no site or outdated site (M10 / M02)

AUTOMATION → professional existing site (chatbot, booking, follow-up)

"""



from __future__ import annotations



from typing import TYPE_CHECKING, Any



from modules.outreach.icebreaker import (

    company_cta_name,

    company_name,

    fallback_icebreaker,

    first_name_from_lead,

)

from utils.contact_greeting import email_greeting_line, subject_name_hint

from modules.outreach.website_pitch import (

    PitchPlan,

    ServiceOffer,

    cache_pitch_on_lead,

    cta_line,

    demo_intro_line,

    offer_line,

    resolve_pitch_plan,

)



if TYPE_CHECKING:

    from modules.lead_finder.scanners.google_maps import MapsScanResult

else:

    MapsScanResult = Any



SIGN_OFF = "Gaurav"





def _followup_offer(lead: MapsScanResult, company: str, plan: PitchPlan) -> str:

    niche = lead.niche.replace("_", " ")

    if plan.service == ServiceOffer.YOUTUBE:
        return (
            f"Just following up — most {niche} creators on YouTube still lose "
            f"sponsorship and client enquiries because there's no clear landing page.\n\n"
            f"I help {company} tighten channel SEO and add a simple page for off-platform leads.\n\n"
            "Happy to share the preview if useful."
        )

    if plan.service == ServiceOffer.WEBSITE:

        if plan.tier.value == "no_site":

            return (

                f"Just following up — most {niche} businesses without a site still lose "

                f"after-hours jobs to whoever answers first.\n\n"

                f"I build a simple web presence plus lead capture for {company}.\n\n"

                "Happy to share the preview if useful."

            )

        return (

            f"Just following up — {company}'s current site likely isn't converting mobile "

            f"visitors the way a {niche} business needs today.\n\n"

            f"I rebuild it to be secure, mobile-first, and built to capture enquiries.\n\n"

            "Happy to share the preview if useful."

        )

    from modules.outreach.website_pitch import _primary_automation

    primary = _primary_automation(lead)
    followups = {
        "customer_support": (
            f"Just following up — {company}'s site looks fine, but support still looks manual.\n\n"
            f"I add AI customer support so common questions get answered right away.\n\n"
            "Happy to share a quick demo if useful."
        ),
        "booking": (
            f"Just following up — {company}'s site looks fine, but booking still goes through the phone.\n\n"
            f"I wire online scheduling so customers pick a time without calling.\n\n"
            "Happy to share a quick demo if useful."
        ),
        "ordering": (
            f"Just following up — {company}'s site looks fine, but there's no way to order online.\n\n"
            f"I add online ordering so customers don't bounce to a competitor.\n\n"
            "Happy to share a quick demo if useful."
        ),
    }
    return followups.get(
        primary,
        (
            f"Just following up — {company}'s site looks fine, but enquiries still look manual.\n\n"
            f"I add AI chat, lead capture, or online booking so nothing sits unanswered.\n\n"
            "Happy to share a quick demo if useful."
        ),
    )





def _close_body(lead: MapsScanResult, first: str, company: str, plan: PitchPlan) -> str:

    if plan.service == ServiceOffer.YOUTUBE:
        radar = f"a channel audit or landing page for {company}"
    elif plan.service == ServiceOffer.WEBSITE:
        radar = f"a new site for {company}" if plan.tier.value == "no_site" else f"a site refresh for {company}"
    else:
        from modules.outreach.website_pitch import _primary_automation

        primary = _primary_automation(lead)
        radar_bits = {
            "customer_support": f"AI customer support for {company}",
            "booking": f"online booking for {company}",
            "ordering": f"online ordering for {company}",
            "scheduling": f"scheduling automation for {company}",
        }
        radar = radar_bits.get(primary, f"chat or booking automation for {company}")

    return (

        f"{email_greeting_line(lead)}\n\n"

        f"Last note from me — I know you're busy.\n\n"

        f"If {radar} is on your radar, I can send a short breakdown.\n\n"

        f"If not, no worries — wish you the best.\n\n"

        f"— {SIGN_OFF}"

    )





def build_email_1(

    lead: MapsScanResult,

    icebreaker: str,

    demo_url: str | None = None,

    sender_name: str = SIGN_OFF,

    plan: PitchPlan | None = None,

) -> dict[str, str]:

    p = plan or resolve_pitch_plan(lead)

    first = first_name_from_lead(lead)
    greeting = email_greeting_line(lead)
    cta_co = company_cta_name(lead)
    sender = sender_name.strip() or SIGN_OFF

    body = f"{greeting}\n\n{icebreaker}\n\n{offer_line(lead, p)}\n"

    if demo_url:

        body += f"\n{demo_intro_line(lead, p)} {demo_url}\n"

    body += f"\n{cta_line(lead, cta_co, p)}\n\n— {sender}"



    return {

        "subject": f"quick question, {subject_name_hint(lead)}",

        "subject_b": "saw something on your site",

        "body": body,

        "sequence_step": 1,

        "send_day": 1,

    }





def build_email_2(lead: MapsScanResult, sender_name: str = SIGN_OFF) -> dict[str, str]:

    company = company_name(lead)

    plan = resolve_pitch_plan(lead)

    body = f"{email_greeting_line(lead)}\n\n{_followup_offer(lead, company, plan)}\n\n— {sender_name}"

    return {

        "subject": f"what this looks like for {company.lower()[:30]}",

        "subject_b": "re: quick follow-up",

        "body": body,

        "sequence_step": 2,

        "send_day": 3,

    }





def build_email_3(lead: MapsScanResult, sender_name: str = SIGN_OFF) -> dict[str, str]:

    first = first_name_from_lead(lead)

    company = company_name(lead)

    plan = resolve_pitch_plan(lead)

    return {

        "subject": f"last one, {subject_name_hint(lead)}",

        "subject_b": "closing the loop",

        "body": _close_body(lead, first, company, plan),

        "sequence_step": 3,

        "send_day": 6,

    }





def build_email_ghost(lead: MapsScanResult, sender_name: str = SIGN_OFF) -> dict[str, str]:

    return {

        "subject": f"quick note, {subject_name_hint(lead)}",

        "subject_b": "timing",

        "body": (

            f"{email_greeting_line(lead)} Totally understand if the timing wasn't right. "

            f"If this ever becomes a priority, I'm here.\n\n— {sender_name}"

        ),

        "sequence_step": 4,

        "send_day": 20,

    }





async def build_sequence_async(

    lead: MapsScanResult,

    your_name: str,

    demo_url: str | None = None,

    steps: int = 3,

    llm: Any | None = None,

    icebreaker: str | None = None,

) -> list[dict[str, str]]:

    from modules.outreach.icebreaker import generate_icebreaker



    plan = cache_pitch_on_lead(lead)

    ib = icebreaker or await generate_icebreaker(lead, demo_url, llm=llm, plan=plan)

    sender = your_name.strip() or SIGN_OFF

    emails = [build_email_1(lead, ib, demo_url=demo_url, sender_name=sender, plan=plan)]

    if steps >= 2:

        emails.append(build_email_2(lead, sender_name=sender))

    if steps >= 3:

        emails.append(build_email_3(lead, sender_name=sender))

    if steps >= 4:

        emails.append(build_email_ghost(lead, sender_name=sender))

    return emails





def build_sequence(

    lead: MapsScanResult,

    your_name: str,

    demo_url: str | None = None,

    steps: int = 3,

    icebreaker: str | None = None,

) -> list[dict[str, str]]:

    plan = cache_pitch_on_lead(lead)

    ib = icebreaker or fallback_icebreaker(lead, demo_url, plan=plan)

    sender = your_name.strip() or SIGN_OFF

    emails = [build_email_1(lead, ib, demo_url=demo_url, sender_name=sender, plan=plan)]

    if steps >= 2:

        emails.append(build_email_2(lead, sender_name=sender))

    if steps >= 3:

        emails.append(build_email_3(lead, sender_name=sender))

    if steps >= 4:

        emails.append(build_email_ghost(lead, sender_name=sender))

    return emails





def format_sequence_export(emails: list[dict[str, str]]) -> str:

    blocks: list[str] = []

    for e in emails:

        step = e.get("sequence_step", 1)

        day = e.get("send_day", "")

        day_label = f" (day {day})" if day else ""

        sub_b = e.get("subject_b", "")

        sub_line = (

            f"SUBJECT A: {e['subject']}\nSUBJECT B: {sub_b}\n"

            if sub_b

            else f"SUBJECT: {e['subject']}\n"

        )

        blocks.append(f"--- EMAIL {step}{day_label} ---\n{sub_line}\n{e['body']}")

    return "\n\n".join(blocks)





def lead_template_variables(

    lead: MapsScanResult,

    icebreaker: str,

    demo_url: str | None,

) -> dict[str, str]:

    plan = cache_pitch_on_lead(lead)

    first = first_name_from_lead(lead)

    company = company_name(lead)

    return {

        "firstName": first,

        "first_name": first,

        "companyName": company,

        "company": company,

        "company_name": company,

        "icebreaker": icebreaker,

        "demo_url": demo_url or "",

        "website": lead.website_url or "",

        "city": lead.city,

        "niche": lead.niche,

        "service_to_pitch": plan.service.value,

        "problem_detected": plan.problem_detected,

        "website_pitch_tier": plan.tier.value,

    }


