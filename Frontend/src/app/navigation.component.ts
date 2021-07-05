import { Component } from '@angular/core';
import { AuthService } from './auth.service';

@Component({
    selector: 'navigation',
    templateUrl: './navigation.component.html',
    styleUrls: []
})

export class NavigationComponent {
    constructor(public authService: AuthService) {}
}