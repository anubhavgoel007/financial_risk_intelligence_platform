# Depository Bank Profile Proposal (Design Only)

## 1. Objective
Support JPM, BAC, and WFC with economically correct, deterministic bank modeling while preserving the existing industrial 21-metric model unchanged.

Design constraints from the completed read-only investigation:
- Industrial profile remains the default and is not redefined.
- Visa is not included in this depository-bank profile.
- Only evidence-backed mappings are allowed.
- Completeness is secondary to economic correctness and reproducibility.

## 2. Bank Profile Architecture
Smallest clean separation:
- Keep the current industrial profile exactly as-is.
- Add a new depository-bank profile selector at metric-resolution policy level.
- Preserve current service boundaries and deterministic behavior.

Proposed separation point:
- Metric resolution policy layer used by financial statement metric selection.
- Profile key controls concept candidates and construction rules.

Profiles:
- industrial_default: current behavior, no changes.
- depository_bank_v1: JPM/BAC/WFC-specific metric definitions and ratio applicability policy.

No implementation in this step.

## 3. Metric-by-Metric Policy (All 21 Canonical Metrics)

Legend:
- SHARED AS-IS: same definition remains valid for banks.
- SAFE bank mapping: direct concept-level substitution supported by evidence.
- BANK-SPECIFIC DEFINITION REQUIRED: deterministic bank definition needed before safe use.
- UNSUPPORTED / REMAIN N/A: not economically meaningful or not safely representable.

| Canonical Metric | Classification | Proposed Policy | Evidence Basis |
|---|---|---|---|
| revenue | BANK-SPECIFIC DEFINITION REQUIRED | Construct bank revenue definition; do not reuse industrial revenue concepts blindly | WFC lacks industrial revenue in FY2024; bank income concepts exist consistently |
| net_income | SHARED AS-IS | Keep NetIncomeLoss | Present and stable across banks |
| operating_income | BANK-SPECIFIC DEFINITION REQUIRED | Define bank operating earnings explicitly; do not force OperatingIncomeLoss | OperatingIncomeLoss absent; NoninterestIncomeOtherOperatingIncome exists but not direct equivalent |
| operating_expenses | SAFE bank mapping | Map to NoninterestExpense | Present FY+quarterly in JPM/BAC/WFC, multi-year consistent |
| gross_profit | UNSUPPORTED / REMAIN N/A | Keep N/A for depository banks | Not a primary bank performance concept |
| interest_expense | BANK-SPECIFIC DEFINITION REQUIRED | Define deterministic construction rule (see section 6) | FY2024 mapped concept missing while component concepts are present |
| income_tax_expense | SHARED AS-IS | Keep IncomeTaxExpenseBenefit | Present and consistent |
| total_assets | SHARED AS-IS | Keep Assets | Present and consistent |
| current_assets | UNSUPPORTED / REMAIN N/A | Do not force industrial current-assets semantics | AssetsCurrent unavailable/inconsistent for banks |
| total_liabilities | SHARED AS-IS | Keep Liabilities | Present and consistent |
| current_liabilities | BANK-SPECIFIC DEFINITION REQUIRED | Do not map directly to mixed current/noncurrent concept without explicit bank definition | Candidate concept includes noncurrent values |
| shareholders_equity | SHARED AS-IS | Keep StockholdersEquity | Present and consistent |
| cash | SAFE bank mapping | Map to CashAndDueFromBanks | Present FY+quarterly across all three banks |
| accounts_receivable | BANK-SPECIFIC DEFINITION REQUIRED | Keep unsupported until explicit economic definition is approved | OtherReceivables or AccountsReceivableNet are not direct equivalents to AccountsReceivableNetCurrent |
| inventory | UNSUPPORTED / REMAIN N/A | Keep N/A | Not economically meaningful for depository banks |
| long_term_debt | BANK-SPECIFIC DEFINITION REQUIRED | Industrial long-term debt alone is insufficient for bank leverage semantics | Inconsistent cross-bank usage as full funding proxy |
| current_debt | BANK-SPECIFIC DEFINITION REQUIRED | Requires bank funding definition, not simple LongTermDebtCurrent reuse | ShortTermBorrowings present but needs formal policy |
| operating_cash_flow | SHARED AS-IS | Keep NetCashProvidedByUsedInOperatingActivities | Present and consistent |
| investing_cash_flow | SHARED AS-IS | Keep NetCashProvidedByUsedInInvestingActivities | Present and consistent |
| financing_cash_flow | SHARED AS-IS | Keep NetCashProvidedByUsedInFinancingActivities | Present and consistent |
| capital_expenditures | BANK-SPECIFIC DEFINITION REQUIRED | Keep for reporting only; do not assume industrial FCF semantics | PPE acquisition exists but bank FCF meaning is ambiguous |

## 4. Revenue Policy (Resolved)
Recommendation: use a constructed bank revenue definition.

Proposed depository bank revenue definition:
- bank_revenue = InterestIncomeExpenseNet + NoninterestIncome

Rationale:
- Both concepts are consistently present across JPM/BAC/WFC in FY and across many years.
- This aligns with depository-bank economic structure better than industrial sales/revenue concepts.
- It is deterministic and auditable from observed SEC concepts.

Not recommended as sole definition:
- InterestIncomeExpenseNet alone: excludes fee/noninterest component.
- NoninterestIncome alone: excludes spread income.
- Industrial Revenues concept set: incomplete/inconsistent for depository banks (especially WFC).

## 5. Operating Income and Operating Expenses Policy
Operating expenses:
- SAFE mapping: operating_expenses -> NoninterestExpense.

Operating income:
- Do not rely on OperatingIncomeLoss.
- Define a bank operating earnings construct explicitly.

Recommended construct:
- bank_operating_income = bank_revenue - NoninterestExpense

Operating margin policy:
- Keep concept as bank-specific variant only if bank_revenue is adopted.
- bank_operating_margin = bank_operating_income / bank_revenue

## 6. Interest Expense Policy
Do not use industrial InterestExpense concept alone for banks.

Recommended deterministic construction:
- primary rule: aggregate component concepts when available:
  - InterestExpenseDeposits
  - InterestExpenseLongTermDebt
  - InterestExpenseShortTermBorrowings
- fallback rule: use InterestExpense only when full component set is unavailable.

Reason:
- FY2024 period selection gaps exist on mapped industrial concepts, while component concepts are present and consistent.

## 7. Debt and Leverage Policy
Industrial debt semantics are not safe for depository banks.

Policy:
- Existing debt_to_equity and debt_to_assets should not use industrial debt definition for banks.
- Bank leverage should be defined using bank funding structure, with explicit policy approval.

Recommended interim bank leverage basis:
- prefer liabilities-based leverage metrics for banks until funding debt definition is approved.
- examples for bank profile (conceptual):
  - liabilities_to_equity = total_liabilities / shareholders_equity
  - liabilities_to_assets = total_liabilities / total_assets

Result:
- existing industrial debt ratios are redefined or disabled for bank profile.

## 8. Liquidity Policy
Current ratio and cash ratio should not be forced from industrial current-assets/current-liabilities semantics.

Policy:
- current_ratio: disable/unsupported for depository-bank profile.
- cash_ratio: disable/unsupported as industrial metric.
- replace with bank-specific liquidity metrics only after explicit definition approval.

## 9. Accounts Receivable Policy
Do not treat OtherReceivables or AccountsReceivableNet as equivalent to industrial accounts_receivable by name only.

Policy:
- accounts_receivable remains bank-specific-definition-required and should stay out of completeness criteria until approved.

## 10. Gross Profit, Inventory, Capex, and Free Cash Flow
- gross_profit: remain N/A for depository banks.
- inventory: remain N/A for depository banks.
- capital_expenditures: keep observable as a raw metric but not used as industrial proxy for bank cash economics without explicit bank definition.
- free_cash_flow ratio: disable or redefine for bank profile; do not reuse industrial formula directly.

## 11. Ratio Policy (Existing Deterministic Ratios)

| Ratio | Policy for Depository Banks | Reason |
|---|---|---|
| net_profit_margin | REDEFINE | Depends on bank_revenue construction |
| operating_margin | REDEFINE | Depends on bank_operating_income and bank_revenue |
| roa | KEEP | Economically meaningful with shared net_income and total_assets |
| roe | KEEP | Economically meaningful with shared net_income and equity |
| current_ratio | DISABLE/UNSUPPORTED | Industrial current-assets/current-liabilities mismatch |
| cash_ratio | DISABLE/UNSUPPORTED | Industrial definition mismatch |
| debt_to_equity | REDEFINE | Industrial debt semantics not suitable |
| debt_to_assets | REDEFINE | Industrial debt semantics not suitable |
| operating_cash_flow_margin | REDEFINE | Requires approved bank_revenue denominator |
| free_cash_flow | DISABLE/UNSUPPORTED (until redefined) | Industrial capex-based FCF not safely transferable |
| operating_cash_flow_to_debt | REDEFINE or DISABLE | Depends on unresolved bank debt definition |

## 12. Training-Feature Implications
Current deterministic feature completeness cannot safely include JPM/BAC/WFC without bank profile definitions.

Features that can remain from shared metrics:
- roa
- roe

Features requiring bank-specific definitions before safe inclusion:
- net_profit_margin
- net_profit_margin_change
- operating_margin
- operating_margin_change
- revenue_growth
- current_ratio
- current_ratio_change
- cash_ratio
- debt_to_equity
- debt_to_equity_change
- debt_to_assets
- operating_cash_flow_margin
- operating_cash_flow_to_debt
- free_cash_flow
- free_cash_flow_growth

Implication:
- Without bank-specific metric and ratio definitions, JPM/BAC/WFC should remain outside the deterministic training cohort.

## 13. Proposed Configuration/Data Structure (No Implementation)
Proposed declarative structure:

- company_profile_registry:
  - JPM -> depository_bank_v1
  - BAC -> depository_bank_v1
  - WFC -> depository_bank_v1
  - V -> industrial_default (separate from depository bank profile)

- metric_policy_by_profile:
  - industrial_default: existing metric concept mapping and selection
  - depository_bank_v1:
    - shared_as_is metrics
    - safe_direct_mappings
    - constructed_metrics (revenue, operating_income, interest_expense)
    - unsupported_metrics

- ratio_policy_by_profile:
  - keep / redefine / disable flags per ratio
  - deterministic formula definitions for redefined bank ratios

## 14. Test Matrix Required Before Enablement
1. JPM/BAC/WFC metric value tests for FY2024 under depository_bank_v1.
2. Cross-bank consistency tests for SAFE and constructed metrics.
3. Multi-year continuity tests for bank revenue, operating expense, and interest expense construction.
4. Ratio validity tests for KEEP and REDEFINE classifications.
5. Explicit unsupported metric tests (gross_profit, inventory, current_ratio family under bank profile).
6. Feature completeness tests showing deterministic behavior for bank profile (including expected unsupported features).
7. Regression tests proving industrial_default outputs for non-bank industrial companies are unchanged.
8. Visa separation tests confirming V does not use depository_bank_v1 policies.

## 15. Rollout Plan (Smallest Sequence)
1. Approve policy decisions in this document.
2. Introduce profile selection mechanism and registry mapping (JPM/BAC/WFC only).
3. Implement metric resolution policy objects for industrial_default and depository_bank_v1.
4. Implement bank-specific constructed metrics (revenue, operating income, interest expense) with deterministic rules and fallbacks.
5. Implement bank ratio policy (keep/redefine/disable) without changing industrial formulas.
6. Add test matrix above and verify industrial regressions remain zero.
7. Run controlled validation on JPM/BAC/WFC only, then decide whether to include banks in training cohort.

## DECISION REQUIRED
Approval is required for the following policy items before implementation:
1. Bank revenue definition: approve bank_revenue = InterestIncomeExpenseNet + NoninterestIncome.
2. Operating income definition: approve bank_operating_income = bank_revenue - NoninterestExpense.
3. Interest expense rule: approve component aggregation with fallback to InterestExpense.
4. Leverage policy: approve liabilities-based bank leverage replacement or specify alternate bank debt definition.
5. Liquidity policy: approve disabling industrial current_ratio and cash_ratio for depository banks pending bank-specific replacements.
6. Accounts receivable policy: approve keeping unsupported until a bank-specific economic definition is formally approved.
7. Visa separation: approve keeping V outside depository_bank_v1.
