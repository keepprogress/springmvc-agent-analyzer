package com.example.web;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.ModelAndView;
import com.example.service.UserService;
import com.example.model.User;

@Controller
@RequestMapping("/users")
public class UserController {

    @Autowired
    private UserService userService;

    @GetMapping("/list")
    public ModelAndView listUsers() {
        return new ModelAndView("users/list");
    }

    @PostMapping("/save")
    public ModelAndView saveUser(@ModelAttribute User user) {
        userService.save(user);
        return new ModelAndView("redirect:/users/list");
    }
}
