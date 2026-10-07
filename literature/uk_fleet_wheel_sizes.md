# UK rental e-scooters: front vs rear wheel size (desk check, 2026-10-07)

Question: in the UK trials, how many rental e-scooter models still have equal front and
rear wheels, despite operators' moves to a larger front wheel?

**Short answer: the evidence does not show many equal-wheel models in the UK. Every UK
fleet model with a front/rear split in a checked source has the larger wheel at the
front. Two widely used models (Voi Voiager 5, older Dott) are given only as "10 in" with no
front/rear split, so it is unknown whether they are equal.** Operators do not publish fleet
counts per model, so a percentage of the national fleet by wheel layout cannot be computed
from public sources.

## 1. The rules
| Rule | Wheel size requirement | Source |
|------|------------------------|--------|
| DfT national trial guidance (updated 17 Jan 2024) | **None.** Tyres "pneumatic or non-pneumatic", "suitable having regard to the use". Stability tests include a **depression 100 cm long x 100 cm wide x 5 cm deep with vertical walls** (exit ramp 45°) | DfT 2024 |
| TfL London trial, Phase 1 (2021) | Front >= 12 in, rear >= 10 in | TfL 2022; Latz 2021 |
| TfL London trial, Phase 2 tender (amended 24 Nov 2022) | Front >= **11 in**, rear >= **9 in** (outer diameter incl. tread), width >= 2 in. Relaxed "further to what TfL now understands is emerging industry practice in vehicle manufacture" | TfL 2022 |

Notes for the paper:
- London is the only trial area found with a wheel-size rule, and it sets a larger minimum
  for the front than the rear. Outside London, equal (or small) wheels are legal.
- The DfT depression test (5 cm deep, 1 m long) is the same kind of obstacle as the
  simulated potholes; the sim shows falls for 10/10 wheels from about 60-70 mm (1000 mm
  long, no suspension), i.e. just above the test depth. Worth a sentence in Part C.

## 2. Who operates where (21 areas on the DfT list, July 2026)
| Operator | Areas (source) |
|----------|----------------|
| Voi | Buckinghamshire (Bucks CC 2024), Cambridge (Cambridge City Council n.d.), Essex (Essex Highways 2025), Gloucestershire (Punchline 2023), Liverpool (LCRCA; current status not re-checked), London (with Lime; recordinglaw 2026), North & West Northants (O'Brien 2022; not re-checked), Oxford (ridden 2026-10-03), Slough (Slough BC 2024), Solent (recordinglaw 2026) |
| Lime | London, Milton Keynes (Get Around MK n.d.), Salford (Salford Now 2025), West Midlands: Birmingham and Warwick campus from April 2026 (Zag Daily 2026) |
| Dott (incl. former TIER) | West of England (Travelwest 2026), Nottingham (Transport Nottingham 2025), Milton Keynes |
| Beryl | Bournemouth & Poole, Brighton & Hove, Cornwall, Leeds, Norwich, Plymouth (Beryl 2026a-c; Zag Daily n.d.) |

- National fleet: 20,719 rental e-scooters (CoMoUK, March 2026). No per-operator split.
- London: two operators, combined maximum fleet 4,715 (TfL 2025).
- Last public per-operator split found: Voi ~10,000 of ~18,000 (56%) in Sept 2021
  (O'Brien 2021). Too old to use for 2026 shares; say "Voi has been the largest UK
  operator" only with that date.

## 3. Models and wheel sizes
| Operator / model | In UK? | Front | Rear | Layout | Source |
|------------------|--------|-------|------|--------|--------|
| Beryl (OKAI ES400 family) | Yes, 6 areas | 12 in | 9 in (ES400A) or 10 in (ES400B) | **Larger front** | Beryl 2020 ("12" front wheels"); Zag Daily 2020 (model = ES400); ScootAPI 2022a,b. Beryl 2026: "a large front wheel and suspension fork for greater stability on uneven roads" |
| Lime Gen4 | Yes (London, MK, Salford, Birmingham) | not stated | not stated | **Larger front** ("Bigger Front Wheel") | Lime 2021. A 12 in figure for both wheels appears on a fan wiki only; don't use it |
| TIER (2022 London model; TIER now part of Dott) | Being replaced by Dott | "large front wheel" | not stated | **Larger front** (stated qualitatively) | Morley 2022 |
| Voi Voiager 7 (2024) | Not confirmed in UK | 12 in | not stated | Probably larger front (unconfirmed) | Startups Magazine 2024 |
| Voi Voiager 5 (2022) | Yes, still newly deployed: Essex 2025; Oxford | "larger front wheel" (vs the previous Voi model); "10 in" | not stated | **Unknown** | Zag Daily 2022; Essex Highways 2025; Levy n.d. (10 in, unsplit) |
| Dott, original model (2020) | Yes at UK launch; current UK model unknown | "10in wheels" | (implied same) | **Possibly equal (10/10)** | Micromobility.biz 2020; Levy n.d. |
| Dott next generation (2022, Brussels) | Unknown | "11.5 in" | not stated | Unknown | CiTTi 2022a |
| Voi Voiager 8 (2025), 9 (2026) | V8: not in UK (FI, FR, DE, NO, ES, SE); V9: will replace earlier generations | not published | not published | Unknown | Treiß 2025; Zag Daily 2026b |

## 4. What can and cannot be said
Can say:
- No national wheel-size standard exists; only London sets one, and it asks for a larger
  front than rear.
- Several UK fleets already use a larger front wheel (Beryl 12/9-10; Lime Gen4; TIER).
- The largest UK operator, Voi, is still deploying a 2022-generation model (Voiager 5) in
  new areas in 2025, and its front/rear sizes are not published.
- An older-generation scooter is still in service in Oxford.

Cannot say (no evidence):
- That "many" UK models have equal wheels. The only candidates are the original Dott
  (10 in, no split) and possibly the Voiager 5.
- Any share of the UK fleet by wheel layout.

Suggested reframing for the paper: the question is not whether operators use a larger
front wheel (several do, and TfL requires one) but **how much larger, and whether a national
minimum is justified**, given that the DfT sets none and fleet sizes range from roughly
10 in to 12 in at the front.

## 5. Action for the user (no fieldwork; a parked scooter is enough)
Read the tyre sidewall markings on a parked Voiager 5, front **and** rear (e.g. "10 x 2.5"
or "60/70-6.5"). If the front is larger than the rear, the simulation's "10/10 = Voiager 5"
baseline is wrong and the configs need relabelling (CLAUDE.md, SIMULATION_METHODS.md,
DOCUMENTATION.md 6.6). Combine this with the planned valve check (pneumatic vs honeycomb).

## Bibliography (Harvard; all accessed 7 October 2026)

Beryl (2020) 'Beryl e-scooters join the family', 21 September. Available at:
https://beryl.cc/news/2020/09/21/beryl-e-scooters-join-family

Beryl (2026a) 'Leeds expands sustainable travel options with launch of e-scooters',
12 March. Available at:
https://beryl.cc/news/2026/03/12/leeds-expands-sustainable-travel-options-launch-government-approved-e-scooters

Beryl (2026b) 'Beryl to launch e-scooters in Plymouth', 22 July. Available at:
https://beryl.cc/news/2026/07/22/beryl-launch-e-scooters-plymouth

Beryl (2026c) 'E-scooters join Beryl BTN Bikes for the first time in Brighton', 23 July.
Available at: https://beryl.cc/news/2026/07/23/e-scooters-join-beryl-btn-bikes-first-time-brighton

Buckinghamshire Council (2024) 'Electric scooters for hire return to Buckinghamshire trial
areas'. Available at:
https://www.buckinghamshire.gov.uk/news/electric-scooters-for-hire-return-to-buckinghamshire-trial-areas
[search snippet only]

Cambridge City Council (n.d.) 'Voi electric bike and scooter trial'. Available at:
https://www.cambridge.gov.uk/voi-electric-bike-and-scooter-trial [search snippet only]

CiTTi Magazine (2022a) 'Dott expands Brussels operations with new e-scooters and second
warehouse', 23 March. Available at:
https://cittimagazine.co.uk/news/micromobility/dott-expands-brussels-operations-with-new-e-scooters-and-second-warehouse.html

CoMoUK (2026) 'Shared e-scooters: overview and benefits' (figures dated March 2026).
Available at: https://www.como.org.uk/shared-e-scooters/overview-and-benefits

Department for Transport (2024) *E-scooter trials: guidance for local areas and rental
operators*, updated 17 January. Available at:
https://www.gov.uk/government/publications/e-scooter-trials-guidance-for-local-areas-and-rental-operators/e-scooter-trials-guidance-for-local-areas-and-rental-operators

Department for Transport (2026) *E-scooter trials: guidance for users*, updated 7 July.
Available at: https://www.gov.uk/guidance/e-scooter-trials-guidance-for-users

Essex Highways (2025) 'Voi announced as new e-scooter trial operator in Essex',
26 August. Available at:
https://www.essexhighways.org/news/voi-announced-as-new-e-scooter-trial-operator-in-essex

Get Around MK (n.d.) 'E-scooter trials'. Available at:
https://www.getaroundmk.org.uk/scooters/e-scooter-trials [search snippet only]

Latz, P. (2021) 'London doubles e-scooter trial with strict requirements', *Micromobility
Report*, 12 August. Available at:
https://micromobilityreport.com.au/infrastructure/bike-scooter-share/london-doubles-e-scooter-trial-with-strict-requirements/

Levy Electric (n.d.) Fleet specifications: 'Voiager 5' and 'Dott E-Scooter'. Available
at: https://fleets.levyelectric.com/vehicles/voi-voiager-5 and
https://fleets.levyelectric.com/vehicles/dott-scooter [aggregator; secondary]

Lime (2021) 'Lime's Gen4 e-scooter rolls into cities worldwide', 16 December. Available
at: https://www.li.me/blog/limes-gen4-e-scooter-rolls-into-cities-worldwide

Micromobility.biz (2020) 'Dott set for UK debut following Government approval', 10 July.
Available at: https://micromobilitybiz.com/dott-set-for-uk-debut-following-government-approval/

Morley, R. (2022) 'Tier introduces upgraded e-scooters in London to boost safety and
accessibility', *Micromobility.biz*, 19 April. Available at:
https://micromobilitybiz.com/tier-introduces-upgraded-e-scooters-to-london-to-boost-safety-and-accessibility

O'Brien, O. (2021) 'Where are shared e-scooters and e-bikes available in the UK?', *Zag
Daily*, 13 September. Available at:
https://zagdaily.com/urban/where-are-shared-e-scooters-and-e-bikes-available-in-the-uk/

O'Brien, O. (2022) 'The definitive guide to the UK's e-scooter trials', *Zag Daily*,
6 May. Available at: https://zagdaily.com/featured/the-definitive-guide-to-the-uks-e-scooter-trials/

Punchline Gloucester (2023) 'New provider for Gloucestershire e-scooters'. Available at:
https://www.punchline-gloucester.com/articles/aanews/new-provider-voi-for-gloucestershire-escooters-gloucester-cheltenham
[search snippet only]

Recordinglaw (2026) 'England e-scooter trial areas: every rental zone listed', 23 July.
Available at: https://www.recordinglaw.com/united-kingdom/driving-laws/e-scooter-laws/rental-trials/
[law-firm explainer; secondary]

Salford Now (2025) 'Salford's e-scooter trial enters final phase', 4 December. Available
at: https://www.salfordnow.co.uk/2025/12/04/salfords-e-scooter-trial-enters-final-phase/
[search snippet only]

ScootAPI (2022a) 'OKAI ES400A - scooter for sharing', 27 October. Available at:
https://scootapi.com/en/vehicles/scooters/okai-es400a/

ScootAPI (2022b) 'OKAI ES400B - scooter for sharing', 27 October. Available at:
https://scootapi.com/en/vehicles/scooters/okai-es400b/
[ScootAPI is a fleet-software vendor; confirm against an OKAI datasheet if possible]

Slough Borough Council (2024) 'E-scooter trial'. Available at:
https://www.slough.gov.uk/parking-roads-travel/e-scooter-trial [search snippet only]

Startups Magazine (2024) 'Voi unveils new scooter: the Voiager 7', 12 April. Available at:
https://startupsmagazine.co.uk/article-voi-unveils-new-scooter-voiager-7

TfL (Transport for London) (2022) *Electric Scooters (E-Scooters) Rental Trial 2 in
London*, Find a Tender notice 2022/S 000-033381 (changes notice), 24 November. Available
at: https://www.find-tender.service.gov.uk/Notice/033381-2022

TfL (2025) *London E-Scooter Trial Phase 3*, preliminary market engagement notice
2025/S 000-058582, 22 September. Available at:
https://www.find-tender.service.gov.uk/Notice/058582-2025

Transport Nottingham (2025) 'Dott e-scooters are now available to hire in Nottingham'.
Available at: https://www.transportnottingham.com/dott-e-scooters-are-now-available-to-hire-in-nottingham/
[search snippet only]

Travelwest (2026) 'Dott begins massive fleet refresh in the West of England', 27 March.
Available at: https://travelwest.info/?p=32403

Treiß, F. (2025) 'Voi stellt neuen E-Tretroller und zwei E-Räder vor', *electrive.net*,
18 March. Available at:
https://www.electrive.net/2025/03/18/voi-stellt-neuen-e-tretroller-und-zwei-e-raeder-vor/

Zag Daily (2020) 'The Beryl e-scooter: a user-friendly way to get from A to Ha!',
5 October. Available at: https://zagdaily.com/tech/the-beryl-e-scooter-a-user-friendly-way-to-get-from-a-to-ha/

Zag Daily (2022) 'Voi releases next-generation e-scooter the Voiager 5', 15 March.
Available at: https://zagdaily.com/tech/voi-releases-next-generation-e-scooter-the-voiager-5/

Zag Daily (2026a) 'Lime to run UK West Midlands micromobility hire scheme'. Available at:
https://zagdaily.com/trends/lime-to-run-uk-west-midlands-micromobility-hire-scheme/
[search snippet only]

Zag Daily (2026b) 'Voi unveils new vehicle family', 26 February. Available at:
https://zagdaily.com/micromobility/voi-unveils-new-vehicle-family/

Entries marked [search snippet only] were seen in search results but the page was not
opened; open them before citing.
