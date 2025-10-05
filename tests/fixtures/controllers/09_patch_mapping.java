package com.example.api;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import org.springframework.beans.factory.annotation.Autowired;
import com.example.service.UserService;
import com.example.dto.UserPatchRequest;
import com.example.model.User;
import javax.validation.Valid;

@RestController
@RequestMapping("/api/users")
public class UserPatchController {

    @Autowired
    private UserService userService;

    @PatchMapping("/{id}")
    public ResponseEntity<User> patchUser(
        @PathVariable Long id,
        @Valid @RequestBody UserPatchRequest patchRequest
    ) {
        User updated = userService.patch(id, patchRequest);
        return ResponseEntity.ok(updated);
    }

    @PatchMapping("/{id}/status")
    public ResponseEntity<Void> updateStatus(
        @PathVariable Long id,
        @RequestParam("status") String status
    ) {
        userService.updateStatus(id, status);
        return ResponseEntity.noContent().build();
    }

    @PatchMapping("/{userId}/preferences/{prefKey}")
    public ResponseEntity<String> updatePreference(
        @PathVariable Long userId,
        @PathVariable String prefKey,
        @RequestBody String value
    ) {
        String result = userService.updatePreference(userId, prefKey, value);
        return ResponseEntity.ok(result);
    }
}
