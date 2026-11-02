// Illustrative Gosu-style reference only. Validate syntax against your Guidewire version.
class ClaimPayoutRule {
  static function calculatePayout(eligibleLoss : BigDecimal, deductible : BigDecimal, aggregateLimit : BigDecimal) : BigDecimal {
    var afterDeductible = eligibleLoss.subtract(deductible).max(BigDecimal.ZERO)
    return afterDeductible.min(aggregateLimit)
  }
}
