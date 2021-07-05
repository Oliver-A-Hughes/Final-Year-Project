import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';

import { RouterModule } from '@angular/router';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { DatePipe } from '@angular/common';
import { AuthService } from './auth.service';

import {BackendService} from './backendService';
import {httpInterceptor} from './httpInterceptor'
import {NavigationComponent} from './navigation.component';
import {HomeComponent} from './home.component';
import {RequestCoverComponent} from './request-cover.component';
import {StaffMembersListComponent} from './staff-members-list.component';
import {StaffMemberComponent} from './staff-member.component';
import {CoverHistoryListComponent} from './cover-history-list.component';
import {CoverHistoryEntryComponent} from './cover-history-entry.component';
import {ShopListComponent} from './shop-list.component';
import {ShopComponent} from './shop.component';

var routes = [
  {
    path: '',
    component: HomeComponent
  },
  {
    path: 'requestcover',
    component: RequestCoverComponent
  },
  {
    path: 'staffmembers',
    component: StaffMembersListComponent 
  },
  {
    path: 'staffmembers/:id',
    component: StaffMemberComponent
  },
  {
    path: 'coverhistory',
    component: CoverHistoryListComponent
  },
  {
    path: 'coverhistory/:id',
    component: CoverHistoryEntryComponent
  },
  {
    path: 'shops',
    component: ShopListComponent
  },
  {
    path: 'shops/:id',
    component: ShopComponent
  }
];

@NgModule({
  declarations: [
    AppComponent,
    HomeComponent,
    NavigationComponent,
    RequestCoverComponent,
    StaffMembersListComponent,
    StaffMemberComponent,
    CoverHistoryListComponent,
    CoverHistoryEntryComponent,
    ShopListComponent,
    ShopComponent
  ],
  imports: [
    BrowserModule,
    HttpClientModule,
    AppRoutingModule,
    RouterModule.forRoot(routes),
    ReactiveFormsModule
  ],
  providers: [BackendService, DatePipe, AuthService,
      {provide: HTTP_INTERCEPTORS,
      useClass: httpInterceptor,
      multi: true}],
      
  bootstrap: [AppComponent]
})
export class AppModule { }
