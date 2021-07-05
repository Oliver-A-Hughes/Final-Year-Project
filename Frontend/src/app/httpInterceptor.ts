import { Injectable } from '@angular/core';
import {HttpInterceptor, HttpRequest, HttpHandler, HttpEvent, HttpErrorResponse} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import {AuthService} from './auth.service';
import { Router } from '@angular/router';

@Injectable({providedIn: 'root'})

export class httpInterceptor implements HttpInterceptor
{
    constructor(private authService : AuthService,
      private router: Router){}

    errorMessage;
    private loginStatus = this.authService.loggedIn;

    getLoginStatus(){
      if (this.authService.loggedIn = true){
        this.loginStatus = true
      }
      else this.loginStatus = false
    }

    handleError(error: HttpErrorResponse)
    {
      if (error.status == 0){
        window.alert("An error has occured Error code: " + error.status)
      }
      else
      {
        this.errorMessage = error.error.error + ". Error code: " + error.status;
        window.alert(this.errorMessage);
      }
      return throwError(error);
    }
    
    intercept(httpRequest: HttpRequest<any>, next: HttpHandler):
    Observable<HttpEvent<any>>{
      if (this.loginStatus === null)
      {
        while (this.loginStatus === null)
        {
          this.getLoginStatus()
        } 
      }

      if (this.authService.loggedIn)
      {
        return next.handle(httpRequest).pipe(catchError(this.handleError))
      }
     else
     {
        this.router.routeReuseStrategy.shouldReuseRoute = () => false;
        this.router.onSameUrlNavigation = 'reload';
        this.router.navigate(['/']);
        window.alert("Please login to continue.")
      } 
    };
}