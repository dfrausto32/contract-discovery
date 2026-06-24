# Protected Anti-Jam Tactical SATCOM Enterprise Mission Management (PATSEMM) Sources Sought Request for Information (RFI)

- **Agency:** DEPT OF DEFENSE.DEPT OF THE AIR FORCE.SPACE SYSTEMS COMMAND.PEO MILITARY COMMUNICATION AND POSITION NAVIGATION TIMING.FA8807 MIL COMM AND PNT SSC/CGK
- **Notice type:** Sources Sought
- **NAICS:** ['517810']
- **Solicitation #:** FA8807-PATSEMM-RFI-001
- **Posted:** 2026-06-23
- **Response deadline:** 2026-07-13
- **SAM.gov link:** https://sam.gov/workspace/contract/opp/0dc97215036f4135a78e5bf92305f3aa/view
- **Candidate fit (AI):** 58/100
- **Generated:** 2026-06-24

---

## Fit Assessment Summary
This is a **moderate fit** for the candidate, but **not a direct domain match**. The opportunity is a **DoD/Air Force Space Systems Command** sources-sought notice for **PATSEMM**, a mission planning and mission operations capability supporting **protected anti-jam tactical SATCOM** across the PATS family of systems, with deployment in **SIPR and NIPR** environments. The work appears to emphasize **mission management software, systems integration, workflow orchestration, security-accredited deployment, and interface development** in a defense SATCOM context.

The candidate aligns well on the **software/platform engineering side** of the requirement: backend and API development, distributed systems, CI/CD automation, cloud/container infrastructure, infrastructure-as-code, DevSecOps, and integration work. Their experience delivering **production systems for a complex DoD software product** is a meaningful positive, especially given the likely need for disciplined delivery, security compliance, and integration into government-owned environments. The candidate also appears well suited for building supporting capabilities such as **mission workflow services, scheduling/allocation engines, metadata services, interface adapters, operator-facing backend services, and secure deployment pipelines**.

## How the Candidate Maps to the Requirement
### Strong alignment areas
- **Backend & API development:** PATSEMM includes mission planning, mission operations, mission product generation, dissemination, and integration with external systems. The candidate is credible for building the **microservices, APIs, orchestration layers, and distributed backend components** needed to support these workflows.
- **DevOps / CI/CD / container platforms:** The RFI stresses rapid, flexible delivery aligned to **Agile and Software Pathway principles**. The candidate’s experience with **GitHub Actions, automated testing, Docker, Kubernetes, release automation, and cloud-native deployment** fits well with a modern software delivery approach.
- **Cloud & infrastructure / IaC:** Although the system may operate in government-defined environments rather than purely commercial cloud, the candidate’s **Terraform/Ansible/cloud deployment** background is relevant for standing up repeatable mission-system environments, lower environments, integration stacks, and deployment automation.
- **Cybersecurity / DevSecOps:** The requirement explicitly references operation within an accredited boundary and spans **SIPR/NIPR** environments. The candidate’s background in **DevSecOps, IAM, vulnerability tooling, FedRAMP/ATO support, RMF/STIG documentation support** is useful for secure delivery and accreditation support, even if SATCOM mission accreditation specifics would require teaming.
- **Systems integration:** The RFI repeatedly mentions interfaces and ICDs, including **MMS to EM&C** and planning-to-operations integration. The candidate has a solid profile for **system integration, interface implementation, API mediation, data translation, and test automation**.
- **Data engineering / analytics:** Mission request ingest, supportability analysis, metadata capture, lineage/provenance, and reporting all have a data-engineering component. The candidate could support **ingest pipelines, scheduling data models, metadata publication, analytics dashboards, and reporting**.

### Partial alignment / needs validation
- **Mission planning and scheduling logic:** The candidate likely has transferable engineering skills for workflow and optimization engines, but the posting references specialized functions such as **supportability analysis, SATCOM resource determination, and scheduling/allocation across constellations**. There is no evidence they already have direct SATCOM mission-planning algorithm experience.
- **Operator mission-planning UX:** The candidate is stronger on backend/platform work than on front-end mission-planning UI. They could support backend services for map-based workflows, but a full end-user planning application may require additional UX/front-end support.
- **Classified operations environment:** Experience with DoD production systems helps, but the notice specifically involves **SIPR-based mission planning and operations**. It is unclear whether the candidate has direct experience deploying and operating software in **classified networks** or handling cross-domain/interface constraints.

## Key Gaps and Risks
The biggest risk is **domain depth**. This opportunity is not just general federal software engineering; it is tied to **anti-jam tactical SATCOM mission management**, protected tactical waveform operations, and integration with specialized systems such as **WGS, PTS-G, PTS-P, Joint Hubs, A3M, and WAMS**. The candidate’s profile does **not** demonstrate clear prior experience in:
- SATCOM or tactical communications mission management
- waveform-specific planning and operations
- military C2 integration for ground elements
- classified mission operations workflows in a Space Force/Air Force operational context
- development of mission-planning products for protected comms

Because the scoring should require a **genuine match to backend development or DevOps/pipeline work**, the candidate clears that bar. However, because the work is highly mission-domain-specific, they are **better positioned as a platform/software/integration contributor than as a standalone prime technical lead for the full PATSEMM scope**.

## Suggested Proposal / Positioning Strategy
The strongest positioning would be to respond as a **software engineering, platform, DevSecOps, and systems integration provider** rather than claiming end-to-end SATCOM mission expertise. A credible response would focus on specific subsections where the candidate can add immediate value:
- **Mission planning backend services:** workflow orchestration, mission request ingest, approval pipelines, metadata handling, auditability, API services, and integration layers
- **Mission operations enablement:** packaging/publishing pipelines, dissemination service integration, observability, and secure deployment automation
- **ICD/interface implementation and testing:** API adapters, message translation, contract testing, integration test harnesses, automated validation
- **Secure software delivery:** DevSecOps pipelines, containerized deployment, IaC-based environment provisioning, RMF/ATO artifact support, IAM/security tooling integration
- **Data and analytics support:** supportability analytics pipelines, dashboards, reporting, provenance/lineage services

For best competitiveness, the candidate should likely **team with a SATCOM/space mission specialist** or a firm with direct **PTW/PATS/mission-operations** experience. In that structure, the candidate can own the **backend architecture, integration platform, DevSecOps, environment automation, and secure software delivery** portions.

## Bottom Line
This is a **credible but not high-confidence fit**. The candidate is technically strong in the exact engineering disciplines needed to build and field modern mission software, especially **backend services, pipelines, cloud/container infrastructure, and security-integrated delivery**. But the opportunity appears to require substantial **defense SATCOM mission-domain expertise** that is not clearly present in the profile. Best fit is as a **teamed technical implementer for software platform, integration, and DevSecOps work**, not as a sole provider of the full PATSEMM mission-management capability.