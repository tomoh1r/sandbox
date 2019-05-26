package io.github.jptomo.fizzbuzz.service;

import lombok.val;
import java.util.StringJoiner;
import org.springframework.stereotype.Component;

@Component
public class FizzBuzzService {
    public String calc(int limit) {
        val joiner = new StringJoiner(" ");
        for (int i = 1; i <= limit; i++) {
            joiner.add(fizzbuzz(i));
        }

        return String.format("### numbers: %s", joiner.toString());
    }

    public static String fizzbuzz(int num) {
        if (num % 15 == 0) {
            return "fizzbuzz";
        } else if (num % 3 == 0) {
            return "fizz";
        } else if (num % 5 == 0) {
            return "buzz";
        } else {
            return String.valueOf(num);
        }
    }
}
