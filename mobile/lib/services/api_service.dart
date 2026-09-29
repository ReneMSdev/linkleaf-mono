import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../core/env.dart';

class AuthException implements Exception {
  final String message;
  const AuthException(this.message);
  @override
  String toString() => 'AuthException: $message';
}

class ApiService {
  static final ApiService instance = ApiService._();

  ApiService._() {
    _dio.interceptors.add(_AuthInterceptor());
  }

  final Dio _dio = Dio(
    BaseOptions(
      baseUrl: Env.apiBaseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 30),
    ),
  );

  Dio get client => _dio;
}

class _AuthInterceptor extends Interceptor {
  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _fetchToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    if (err.response?.statusCode == 401) {
      try {
        final token = await _fetchToken(forceRefresh: true);
        if (token == null) {
          throw const AuthException('Session expired — please log in again');
        }
        err.requestOptions.headers['Authorization'] = 'Bearer $token';
        final response = await Dio().fetch(err.requestOptions);
        handler.resolve(response);
      } on AuthException catch (e) {
        handler.reject(
          DioException(requestOptions: err.requestOptions, error: e),
        );
      } catch (_) {
        handler.reject(
          DioException(
            requestOptions: err.requestOptions,
            error: const AuthException('Session expired — please log in again'),
          ),
        );
      }
      return;
    }
    handler.next(err);
  }

  Future<String?> _fetchToken({bool forceRefresh = false}) async {
    try {
      return await FirebaseAuth.instance.currentUser?.getIdToken(forceRefresh);
    } catch (_) {
      return null;
    }
  }
}
