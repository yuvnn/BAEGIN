package com.baegin.auth.service;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class UserStore {

    public record UserRecord(String userId, String email, String name, List<String> keywords, String passwordHash) {}

    private final ConcurrentHashMap<String, UserRecord> byEmail = new ConcurrentHashMap<>();
    private final BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();

    public UserRecord register(String email, String name, List<String> keywords, String rawPassword) {
        if (byEmail.containsKey(email)) {
            throw new IllegalStateException("already exists");
        }
        String hash = encoder.encode(rawPassword);
        UserRecord user = new UserRecord(UUID.randomUUID().toString(), email,
                name != null ? name : email.split("@")[0],
                keywords != null ? keywords : List.of(),
                hash);
        byEmail.put(email, user);
        return user;
    }

    public boolean verifyPassword(String email, String rawPassword) {
        UserRecord user = byEmail.get(email);
        if (user == null) return false;
        return encoder.matches(rawPassword, user.passwordHash());
    }

    public UserRecord find(String email) {
        return byEmail.get(email);
    }
}
