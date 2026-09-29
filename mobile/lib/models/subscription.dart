enum SubscriptionTier { free, pro }

class Subscription {
  final SubscriptionTier tier;

  const Subscription({required this.tier});
}
