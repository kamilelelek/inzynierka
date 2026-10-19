package pl.pk.smarthome.service;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import pl.pk.smarthome.config.JwtProperties;
import pl.pk.smarthome.dto.TokenResponse;
import pl.pk.smarthome.entity.AppUser;

@Service
@RequiredArgsConstructor
public class JwtService {

	private final JwtProperties properties;

	public TokenResponse generateToken(AppUser user) {
		// TODO: JwtEncoder, claims: sub = username, role, exp = teraz + properties.expiration()
		throw new UnsupportedOperationException("TODO");
	}

}
