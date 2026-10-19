package pl.pk.smarthome.service;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import pl.pk.smarthome.dto.LoginRequest;
import pl.pk.smarthome.dto.TokenResponse;
import pl.pk.smarthome.repository.AppUserRepository;

@Service
@RequiredArgsConstructor
public class AuthService {

	private final AppUserRepository userRepository;
	private final JwtService jwtService;

	public TokenResponse login(LoginRequest request) {
		// TODO: znaleźć użytkownika, sprawdzić hasło (PasswordEncoder), wygenerować token
		throw new UnsupportedOperationException("TODO");
	}

}
