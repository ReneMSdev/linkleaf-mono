import 'package:flutter/foundation.dart';

// Source of truth for the user's subscription tier.
// isPremium matches the premium entitlement field returned by the API.
// It drives all conditional UI in CardSheet — branding bar and locked
// placeholders when false, portfolio carousel + résumé when true.
// Wire up: call setTier(isPremium: response.entitlements.contains('premium'))
// after fetching the subscription and call notifyListeners().
class SubscriptionProvider extends ChangeNotifier {
  bool _isPremium = false;

  bool get isPremium => _isPremium;

  void setTier({required bool isPremium}) {
    if (_isPremium == isPremium) return;
    _isPremium = isPremium;
    notifyListeners();
  }
}
