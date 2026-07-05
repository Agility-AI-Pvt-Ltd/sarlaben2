def seconds_from_bytes(
    byte_count: int, sample_rate: int = 16000, bytes_per_sample: int = 2
) -> float:
    if sample_rate <= 0 or bytes_per_sample <= 0:
        return 0.0
    return byte_count / (sample_rate * bytes_per_sample)
