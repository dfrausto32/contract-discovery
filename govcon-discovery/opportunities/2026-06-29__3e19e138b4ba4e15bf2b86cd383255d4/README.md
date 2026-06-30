# Persistent Cyber Training Environment (PCTE) Cyber Range Development Software Application Project (Simulated Internet for Cyber Range Training Events)

- **Agency:** DEPT OF DEFENSE.DEPT OF THE ARMY.AMC.ACC.ACC-CTRS.ACC-ORLANDO.W6QK ACC-ORLANDO
- **Notice type:** Sources Sought
- **NAICS:** ['541519']
- **Solicitation #:** PCTERange-FY2026
- **Posted:** 2026-06-29
- **Response deadline:** 2026-07-14
- **SAM.gov link:** https://sam.gov/workspace/contract/opp/3e19e138b4ba4e15bf2b86cd383255d4/view
- **Candidate fit (AI):** 78/100
- **Generated:** 2026-06-30

---

## Fit Assessment Summary
This is a **strong but not perfect fit** for the candidate. The opportunity centers on a **simulated internet / cyber range capability** for the Army's Persistent Cyber Training Environment (PCTE), with emphasis on **scalability, isolation, automation, observability, security integration, and deployment into an existing virtualized and software-defined infrastructure**. The candidate aligns well on the **software engineering, platform engineering, cloud/infrastructure, DevSecOps, automation, and integration** dimensions, but appears to have **less explicit direct experience in cyber range product development, large-scale traffic generation, SDN-specific engineering (NSX-T/F5), or protocol-level internet emulation**. Because this notice is a **Sources Sought/RFI**, that gap is more manageable if positioned correctly.

## Opportunity Summary
PCTE is seeking vendors that can help deliver or inform a **realistic, controlled, isolated, and scalable simulated internet capability** (Grey Space) for cyber training events. The environment must support:
- **Dynamic provisioning** of cyber-range topologies and services
- **Background traffic generation at scale** with measurable throughput/session capacity
- **Realistic internet behaviors and services** (DNS, web, email, cloud, user activity, adversary infrastructure)
- **Security controls and isolation**
- **Integration** with existing PCTE architecture, including hardened control-plane services and isolated event-plane environments
- **Observability, logging, replay, and reporting**
- Compatibility with an ecosystem using **VMware Cloud Foundation, NSX-T, F5, and Red Hat SSO**

## How the Candidate Maps to the Requirement
### Strong alignment
- **Backend & distributed systems**: The candidate has relevant experience designing **production microservices, REST APIs, and distributed systems**, which maps well to a platform that needs orchestration services, scenario-generation services, control-plane APIs, telemetry collection, and reporting interfaces.
- **DevOps / CI/CD / automation**: This is one of the candidate's strongest matches. PCTE emphasizes **repeatability, reset, rapid provisioning, and controlled deployment**, all of which benefit from strong CI/CD, test automation, containerization, and release engineering.
- **Cloud & infrastructure-as-code**: The candidate's Terraform/Ansible and cloud deployment background aligns with the need to **instantiate environments on demand**, manage infrastructure consistently, and support future on-prem/cloud integration.
- **Cybersecurity / DevSecOps**: The candidate has practical experience with **FedRAMP/ATO support, STIG/RMF documentation, IAM, vulnerability tooling, and security integration into pipelines**. That is highly relevant to PCTE's emphasis on **hardened services, isolation, access control, sanitization, and integration with security tools**.
- **Data engineering & analytics**: PCTE requires **logging, metrics, after-action review, replay support, and reporting**. The candidate's analytics and data pipeline background is a solid fit for telemetry aggregation, dashboarding, and exercise analytics.
- **Production experience in a complex DoD software product**: This materially improves fit. It suggests familiarity with defense delivery constraints, accreditation context, and operating in a more controlled mission environment.

### Partial alignment / likely stretch areas
- **Cyber range / simulated internet specialization**: The opportunity is not just general software development; it is focused on **internet emulation, adversary infrastructure, background traffic realism, and exercise support**. The candidate summary does not show direct prior delivery of a cyber range or grey-space platform.
- **Network/protocol realism**: The RFI specifically calls out advanced behaviors like **DNSSEC validation, BGP hijacking scenarios, HTTPS inspection/decryption, and localized root-CA hierarchies**. The candidate may be able to support the platform engineering around these capabilities, but there is no stated deep expertise in building those protocol simulations.
- **Platform-specific stack**: No explicit experience is listed with **VMware Cloud Foundation, NSX-T, F5, or Red Hat SSO**. Those may be learnable, but they are important integration points.
- **High-scale traffic generation benchmarks**: The RFI wants maximum throughput and concurrent session generation limits. The candidate looks capable on automation and systems integration, but not obviously as the architect of a specialized traffic-generation engine.

## Suggested Positioning for a Proposal / Response
The best positioning is **not** to present the candidate as a pure cyber-range product specialist, but rather as a **platform engineering, automation, integration, and secure delivery lead** for a simulated internet capability.

A credible response would emphasize that the candidate can help deliver:
- **Control-plane services** for scenario orchestration, provisioning APIs, user/admin workflows, and reporting
- **Infrastructure automation** for repeatable deployment of event-plane resources, services, and exercise topologies
- **DevSecOps pipelines** for secure build/test/release of range components
- **Observability and analytics** for exercise telemetry, dashboards, and after-action review data flows
- **Security integration and compliance support** for IAM, logging, scanning, hardening, and accreditation artifacts
- **Cloud/on-prem integration patterns** to support current and future deployment models

If responding as part of a team, the ideal complement would be a partner with proven depth in:
- cyber range product development
- SDN / NSX-T / F5 engineering
- internet-scale traffic generation and protocol simulation
- adversary emulation and training content

## Risks and Unknowns
- **Biggest risk**: lack of explicit, demonstrated experience in **simulated internet engineering or cyber range development**.
- **Technical stack gap**: no stated hands-on work with **VMware Cloud Foundation, NSX-T, F5, Red Hat SSO**.
- **Protocol emulation depth**: unclear whether the candidate can independently lead implementation of **DNSSEC, BGP hijack simulation, TLS interception, or root-CA hierarchy simulation**.
- **Domain fit vs. interest**: the candidate prefers **civilian federal agency work**, while this is a **DoD cyber training** opportunity. They still have relevant defense experience, but this is slightly less aligned with stated preference.

## Bottom Line
This is a **good fit for a platform/software/DevSecOps role within the effort**, especially for orchestration, secure automation, observability, integration, and control-plane/backend delivery. It is a **weaker fit if the expectation is a lead architect for the core simulated-internet / traffic-generation / SDN cyber-range engine itself**. Best pursued as a **teaming role or as a scoped technical lead for backend, infrastructure automation, and secure platform integration**.