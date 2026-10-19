package pl.pk.smarthome.entity;

import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

// Odczyt DHT22 (topic climate/telemetry)
@Entity
@Table(name = "climate_readings", indexes = @Index(columnList = "measuredAt"))
@Getter
@Setter
@NoArgsConstructor
public class ClimateReading {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@Column(nullable = false)
	private Double temperature;

	@Column(nullable = false)
	private Double humidity;

	@Column(nullable = false)
	private Instant measuredAt;

}
