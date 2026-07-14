# Persistent Cyber Training Environment (PCTE) Cyber Range Development Software Application Project (Simulated Internet for Cyber Range Training Events)

- **Agency:** DEPT OF DEFENSE.DEPT OF THE ARMY.AMC.ACC.ACC-CTRS.ACC-ORLANDO.W6QK ACC-ORLANDO
- **Notice type:** Sources Sought
- **NAICS:** ['541519']
- **Solicitation #:** PCTERange-FY2026
- **Posted:** 2026-07-13
- **Response deadline:** 2026-07-21
- **SAM.gov link:** https://sam.gov/workspace/contract/opp/445cc251b3e343a995619b7f2cfedf71/view
- **Candidate fit (AI):** 78/100
- **Generated:** 2026-07-14

---

## Fit Assessment Summary
This is a **strong but not perfect fit** for the candidate. The opportunity is a **DoD cyber range / simulated internet platform** effort centered on **software-driven environment provisioning, isolation, scalability, automation, security integration, and observability**. The candidate aligns well on the **backend/platform engineering, DevOps, cloud/infrastructure, containerization, Kubernetes, IaC, security automation, and production systems delivery** aspects. The candidate also has relevant credibility from delivering **production systems for a complex DoD software product**, which helps significantly in this defense-oriented environment.

The biggest strengths are in building the **automation and orchestration layers** behind a cyber range: provisioning services, APIs, CI/CD, infrastructure-as-code, cloud/on-prem deployment patterns, security tooling integration, IAM, logging, dashboards, and environment reset/rebuild workflows. The biggest gap is that the notice appears to care deeply about **specialized cyber range/network simulation capabilities**—for example **realistic background traffic generation at scale, protocol-state fidelity, DNSSEC validation, BGP hijack scenarios, HTTPS inspection/decryption, root-CA hierarchy simulation, NSX-T/VMware Cloud Foundation/F5-specific integration, and possibly high-throughput network emulation engineering**. Those are not explicitly in the candidate's background as described.

## How the Candidate Maps to the Requirement
### Strong alignment
- **Backend & API development** maps well to the need for **dynamic topology creation, service orchestration, provisioning interfaces, automation services, dashboards, training support services, and integration APIs**.
- **DevOps & CI/CD** is highly relevant because PCTE needs **repeatable environment creation, automated testing, release automation, containerized services, and reliable deployment workflows**.
- **Cloud & infrastructure** experience strongly supports **on-prem/cloud hybrid deployment patterns, IaC, modular environment buildout, and scalable operations**.
- **Cybersecurity & Zero Trust** maps well to **isolated operations, access controls, IAM, security tooling integration, compliance-minded architecture, logging, and secure software delivery**.
- **Data engineering & analytics** is useful for **comprehensive logging, after-action review pipelines, metrics collection, reporting, and observability dashboards**.
- **DoD product delivery experience** is a meaningful advantage for understanding **mission users, accreditation realities, operational rigor, and defense program execution**.

### Partial alignment / likely stretch areas
- The requirement emphasizes **simulated internet realism and traffic generation at scale**, including measurable **throughput and concurrent session limits**. The candidate's profile does not directly establish experience with **packet-level traffic generation platforms, ISP/backbone simulation, botnet/C2 emulation, or synthetic user population modeling**.
- The notice references a very specific platform ecosystem: **VMware Cloud Foundation, NSX-T, F5 edge firewalls, Red Hat SSO**. The candidate has broadly relevant infra/cloud skills, but **direct platform-specific depth is not stated**.
- Advanced network/security scenarios such as **BGP hijacking, DNSSEC validation, HTTPS inspection/decryption, and localized autonomous root-CA hierarchies** suggest a need for **deep network engineering and cyber range content expertise** beyond general software engineering.

## Suggested Positioning for a Proposal
Position the candidate primarily as a **platform/software automation and integration lead** rather than as the sole cyber-range simulation SME.

A credible proposal angle would be:
- **Automated environment orchestration** for simulated range services and scenarios
- **Provisioning APIs/microservices** for repeatable deployment and reset of training environments
- **Containerized service delivery** for simulated public services and support tooling
- **Infrastructure-as-code and deployment pipelines** for control-plane and event-plane supporting components
- **Security integration and observability**, including logs, metrics, dashboards, auditability, and after-action data pipelines
- **Interoperability/integration engineering** across existing PCTE tools and future components

Best fit is likely as part of a **teaming arrangement** with a partner that brings proven depth in:
- cyber range design/content
- high-scale traffic generation
- NSX-T / VMware / F5 implementation
- advanced network emulation and protocol simulation

## Risks / Unknowns
- **Core cyber range specialization gap:** unclear direct experience with simulated internet platforms or grey-space environments.
- **Platform-specific gap:** NSX-T, VMware Cloud Foundation, F5, and Red Hat SSO experience is not explicitly confirmed.
- **Network-protocol realism gap:** no stated evidence of hands-on work with BGP/DNSSEC/TLS interception simulation or internet-scale traffic modeling.
- **Agency preference:** the candidate prefers civilian agencies, while this is a **defense-specific** opportunity; still viable given prior DoD work.

## Bottom Line
This candidate is a **good technical fit for the software platform, DevOps, integration, security automation, and observability portions** of the effort, but only a **partial fit for the highly specialized cyber-range/network-simulation core** unless supported by teammates or prior directly relevant range experience not listed here. As a prime for the entire scope, the fit is **moderately strong but incomplete**; as a **platform engineering / DevSecOps / integration lead within a broader team**, the fit is **strong**.