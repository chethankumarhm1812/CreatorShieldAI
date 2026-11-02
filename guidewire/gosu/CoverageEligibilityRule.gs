// Illustrative Gosu-style reference only. Validate syntax against your Guidewire version.
class CoverageEligibilityRule {
  static function isCovered(policy : Policy, incidentDate : Date, incidentType : String) : boolean {
    return policy.Status == PolicyStatus.TC_INFORCE
      and incidentDate >= policy.PeriodStart
      and incidentDate <= policy.PeriodEnd
      and {"ACCOUNT_TAKEOVER", "MALWARE_COMPROMISE", "RANSOMWARE", "COVERED_RESTRICTION"}.contains(incidentType)
  }
}
