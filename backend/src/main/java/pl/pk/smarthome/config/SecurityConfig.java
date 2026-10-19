package pl.pk.smarthome.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

	// TODO: SecurityFilterChain: stateless, /api/auth/** bez logowania, reszta wymaga JWT (oauth2ResourceServer)
	// TODO: PasswordEncoder (BCrypt)
	// TODO: JwtEncoder i JwtDecoder (HMAC, klucz z JwtProperties.secret)
	// TODO: CORS dla frontendu

}
