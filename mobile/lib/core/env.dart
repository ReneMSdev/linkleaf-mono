enum AppEnvironment { dev, staging, prod }

abstract class Env {
  static const String _envStr = String.fromEnvironment(
    'ENV',
    defaultValue: 'dev',
  );
  static const String _apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8080',
  );
  static const String _appName = String.fromEnvironment(
    'APP_NAME',
    defaultValue: 'LinkLeaf Dev',
  );

  static AppEnvironment get environment => switch (_envStr) {
    'prod'    => AppEnvironment.prod,
    'staging' => AppEnvironment.staging,
    _         => AppEnvironment.dev,
  };

  static String get apiBaseUrl  => _apiBaseUrl;
  static String get appName     => _appName;
  static bool   get isProduction => environment == AppEnvironment.prod;
  static bool   get isDev        => environment == AppEnvironment.dev;
}
