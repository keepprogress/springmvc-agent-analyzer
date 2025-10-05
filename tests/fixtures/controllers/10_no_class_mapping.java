package com.example.web;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;
import com.example.service.HomeService;

@Controller
public class HomeController {

    @Autowired
    private HomeService homeService;

    @GetMapping("/")
    public String home() {
        return "index";
    }

    @GetMapping("/about")
    public String about() {
        return "about";
    }

    @GetMapping("/contact")
    public String contact() {
        return "contact";
    }

    @PostMapping("/contact/submit")
    public String submitContact(
        @RequestParam("name") String name,
        @RequestParam("email") String email,
        @RequestParam("message") String message
    ) {
        homeService.handleContact(name, email, message);
        return "redirect:/contact/success";
    }
}
