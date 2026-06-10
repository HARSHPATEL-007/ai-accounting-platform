import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:connectivity_plus/connectivity_plus.dart';

class ConnectivityState {
  final bool isConnected;
  final ConnectivityResult? lastResult;

  ConnectivityState({this.isConnected = true, this.lastResult});
}

class ConnectivityProvider extends Cubit<ConnectivityState> {
  ConnectivityProvider() : super(ConnectivityState()) {
    Connectivity().onConnectivityChanged.listen((result) {
      emit(ConnectivityState(
        isConnected: result != ConnectivityResult.none,
        lastResult: result,
      ));
    });
  }
}
