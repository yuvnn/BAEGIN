package com.baegin.auth.dto;

import java.util.List;

public record RegisterRequest(String email, String name, String password, List<String> keywords, String otp) {}
