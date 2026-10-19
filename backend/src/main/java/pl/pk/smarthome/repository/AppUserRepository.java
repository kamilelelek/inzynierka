package pl.pk.smarthome.repository;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import pl.pk.smarthome.entity.AppUser;

public interface AppUserRepository extends JpaRepository<AppUser, Long> {

	Optional<AppUser> findByUsername(String username);

}
