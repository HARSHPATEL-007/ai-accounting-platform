import 'package:flutter_bloc/flutter_bloc.dart';

class AuthState {
  final bool isAuthenticated;
  final String? userId;
  final String? clientId;

  AuthState({this.isAuthenticated = false, this.userId, this.clientId});

  AuthState copyWith({bool? isAuthenticated, String? userId, String? clientId}) {
    return AuthState(
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      userId: userId ?? this.userId,
      clientId: clientId ?? this.clientId,
    );
  }
}

class AuthProvider extends Cubit<AuthState> {
  AuthProvider() : super(AuthState());

  void login(String userId, String clientId) {
    emit(state.copyWith(isAuthenticated: true, userId: userId, clientId: clientId));
  }

  void logout() {
    emit(AuthState());
  }
}
