/*
 * Copyright (C) Rida Bazzi, 2016
 * Edited by Joshua Elkins, 2023
 *
 * Do not share this file with anyone
 */
#include <iostream>
#include <istream>
#include <vector>
#include <string>
#include <cctype>
#include <stdlib.h>
#include <string.h>

#include "lexer.h"
#include "inputbuf.h"
#include "parser.h"
using namespace std;

// Functions outside the class
struct scopeResolve {
 string scope;
 scopeResolve* next;
};

struct sTableEntry {
    string name;
    string scope;
    int type;
};

struct sTable {
sTableEntry* item;
sTable *prev;
sTable *next;
bool printed = false;
};

sTable* symbolTable;
string currentScope;
scopeResolve* scopeTable;
int generic_type = 3;

void addList(string lexeme, int type){
   if(symbolTable == NULL){
      sTable* newEntry =  new sTable;
      sTableEntry* newItem = new sTableEntry;
      newItem->name = lexeme;
      newItem->scope = currentScope;
      newItem->type = type;

      newEntry->item = newItem;
      newEntry->next = NULL;
      newEntry->prev = NULL;
      symbolTable = newEntry;
      }else{
         sTable* temp = symbolTable;
         while(temp->next != NULL){
            temp = temp->next;
         }
         sTable* newEntry =  new sTable;
        sTableEntry* newItem = new sTableEntry;
         newItem->name = lexeme;
         newItem->scope = currentScope;
         newItem->type = type;

         newEntry->item = newItem;
         newEntry->next = NULL;
         newEntry->prev = temp;
         temp->next = newEntry;
   }
}

void printScope(void){
    scopeResolve* temp = scopeTable;

    while(temp->next != NULL){
        temp = temp->next;
    }
}


void printList(void){
     sTable* temp = symbolTable;

    while(temp != NULL){
        string type;
        int type_no = temp->item->type;
        switch (temp->item->type)
        {
        case 0:
            type = "int";
            break;
        case 1:
            type = "real";
            break;
        case 2:
            type = "bool";
            break;
        
        default:
        type = "?";
            break;
        }
        if(type_no>3 && temp->printed==false){
            cout<<temp->item->name;
            temp->printed = true;
            while(temp!=NULL){
                if(temp->printed==true || temp->item->type != type_no){
                    temp = temp->next;
                    
                }
                else{
                    cout<<", "<<temp->item->name;
                    temp->printed = true;
                    temp = temp->next;
                }
            }
            cout<<": "<<type<<" #"<<endl;
            temp = symbolTable;
        }
        else if(temp->printed == false){
            cout<<temp->item->name<<": "<<type<<" #"<<endl;
            temp->printed = true;
            temp = temp->next;
        }
        else temp = temp->next;
    }
}

int searchList(string iD){// add an argument to accept a type
    
    sTable* temp = symbolTable;

        if(temp == NULL){
            addList(iD, generic_type);
            return generic_type++;
        }
        while(temp != NULL){
            if(temp->item->name == iD){
                return temp->item->type;
            }
            temp = temp->next;
        }

        addList(iD, generic_type);
        return generic_type++;
    
}

void update(int old_type, int new_type){
    sTable* temp = symbolTable;
    while(temp!=NULL){
        if(temp->item->type == old_type) temp->item->type = new_type;
        temp = temp->next;
    }
}

vector<string> var_decl;

// parse var_list
int Parser::parse_varlist(void){
    token = lexer.GetToken();
    int tempI;
    var_decl.push_back(token.lexeme);
    // Check First set of ID
    if(token.token_type == ID){
        token = lexer.GetToken();
        if(token.token_type == COMMA){
            tempI = parse_varlist();
        }else if(token.token_type == COLON){
            tempTokenType = lexer.UngetToken(token);
        }else{
        }
    }else{
        exit(1);
    }    
    return(0);
}

int Parser::parse_unaryOperator(void){
    token = lexer.GetToken();
    
    if(token.token_type != NOT){
        exit(1);
    }
    return token.token_type;
}

int Parser::parse_binaryOperator(void){
    token = lexer.GetToken();
    //keep track of the number of bin operations in type
    if(token.token_type == PLUS  ){
    }else if(token.token_type == MINUS ){
    }else if(token.token_type == MULT){
    }else if(token.token_type == DIV ){
    }else if(token.token_type == GREATER){
    }else if(token.token_type == LESS  ){
    }else if(token.token_type == GTEQ ){
    }else if(token.token_type == LTEQ){
    }else if(token.token_type == EQUAL ){
    }else if(token.token_type == NOTEQUAL){
    }else{
        exit(1);
    }
    return token.token_type;
}



int Parser::parse_primary(void){
    token = lexer.GetToken();
    
    if(token.token_type == ID  ){
        // search list for the token. If token available then return the type of the token. if not then add the token to the list
        // make its scope = "h" and make its type = -1;
        return searchList(token.lexeme);
    }else if(token.token_type == NUM ){
        return 0;
    }else if(token.token_type == REALNUM){
        return 1;
    }else if(token.token_type == TR ){
        return 2;
    }else if(token.token_type == FA){
        return 2;
    }
    exit(1);
}

int Parser::parse_expression(void){
    int tempI;
    int tempI1, tempI2;
    token = lexer.GetToken();
    
    if(token.token_type == ID || token.token_type == NUM || token.token_type == REALNUM || token.token_type == TR || token.token_type == FA ){
        tempTokenType = lexer.UngetToken(token);
        return parse_primary();
    }else if(token.token_type == PLUS || token.token_type == MINUS || token.token_type == MULT || token.token_type == DIV){
        
        tempI1 = parse_expression();
        tempI2 = parse_expression();

        if(tempI1 != tempI2 && (tempI1<3 && tempI2<3)){
            cout << "TYPE MISMATCH " << token.line_no << " C2" << endl;
            exit(1);
        }else if(tempI1<3 && tempI2>2){
            update(tempI2, tempI1);
            return tempI1;
        }else if(tempI1>2 && tempI2<3){
            update(tempI1, tempI2);
            return tempI2;
        }else{
            update(tempI2, tempI1);
            return tempI1;
        }

    }else if(token.token_type == GREATER || token.token_type == LESS || token.token_type == GTEQ || token.token_type == LTEQ || token.token_type == EQUAL || token.token_type == NOTEQUAL){
        tempI1 = parse_expression();
        tempI2 = parse_expression();

        if(tempI1 != tempI2 && (tempI1<3 && tempI2<3)){
            cout << "TYPE MISMATCH " << token.line_no << " C2" << endl;
            exit(1);
        }else if(tempI1<3 && tempI2>2){
            update(tempI2, tempI1);
            return 2;
        }else if(tempI1>2 && tempI2<3){
            update(tempI1, tempI2);
            return 2;
        }else{
            update(tempI1, tempI2);
            return 2;
        }
    }
    else if(token.token_type == NOT){
        tempI = parse_expression();
        if(tempI==2){
            return 2;
        }else if(tempI>2){
            update(tempI, 2);
            return 2;
        }else{
            cout << "TYPE MISMATCH " << token.line_no << " C3" << endl;
            exit(1);
        }
        //if parse expression returns an ID and type of that ID is -1 then make it 2 by using search list
        // if tempI2 != 2 and != -1 then Type mismatch token.line_no C3????
    }
    exit(1);
}


int Parser::parse_assstmt(void){
    int tempI;
    token = lexer.GetToken();

    if(token.token_type == ID){
        // search for the token in the searchList --> the token is available, leftType = type of the available token
        // it is not available in the searchList, add the token to the list, make its type = -1; make its scope = "h".
        int lhs = searchList(token.lexeme);
        token = lexer.GetToken();
        if(token.token_type == EQUAL){
             token = lexer.GetToken();  
             if(token.token_type == ID || token.token_type == NUM || token.token_type == REALNUM || token.token_type == TR || token.token_type == FA || token.token_type == PLUS || token.token_type == MINUS || token.token_type == MULT || token.token_type == DIV || token.token_type == LESS || token.token_type == GREATER || token.token_type == GTEQ || token.token_type == LTEQ || token.token_type == EQUAL || token.token_type == NOTEQUAL || token.token_type == NOT){
                tempTokenType = lexer.UngetToken(token);
                tempI = parse_expression();
                //rType right type of an assigment tempI.
                //check for C1. if ltype == rtype then fine if not then TYPE MISMATCH token.line_no C1
                // if any one of lType or rType is -1 then should not throw type mismatch. 
                // if lType != -1 && rType is -1 then you search for left ID token to extract its type. searchList should return type. 
                // you have to use search list again with the right token to update the right token's type to lType 
                if(lhs != tempI && (lhs<3 && tempI<3)){
                    cout << "TYPE MISMATCH " << token.line_no << " C1" << endl;
                    exit(1);
                }else if(lhs<3 && tempI>2){

                    update(tempI, lhs);
                    tempI = lhs;
                }else if(lhs>2 && tempI<3){
                    update(lhs, tempI);
                }else{
                    update(lhs, tempI);
                    tempI = lhs;
                }
                token = lexer.GetToken();
                if(token.token_type == SEMICOLON){
                    return tempI;
                }else{
                    exit(1);    
                 }
             }else{
                exit(1);    
             }  
        }else{
            exit(1);    
        }  
    }else{
        exit(1);    
    }
}

int Parser::parse_case(void){
    int tempI;
    token = lexer.GetToken();

    if(token.token_type == CASE ){
        token = lexer.GetToken();
        if(token.token_type == NUM){
            token = lexer.GetToken();
            if(token.token_type == COLON){
                tempI = parse_body();
            }else{
                exit(1);
            }
        }else{
            exit(1);
        }
    }else{
        exit(1);
    }
    return 0;
}

int Parser::parse_caselist(void){
    
    int tempI;
    token = lexer.GetToken();
    if(token.token_type == CASE){
        tempTokenType = lexer.UngetToken(token);
        tempI = parse_case();
        token = lexer.GetToken();
        if(token.token_type == CASE){
            tempTokenType = lexer.UngetToken(token);
            tempI = parse_caselist();
        }else if(token.token_type == RBRACE){
            tempTokenType = lexer.UngetToken(token);
        }
    }
    return(0);
}


int Parser::parse_switchstmt(void){
    int tempI;
    
    token = lexer.GetToken();
    if(token.token_type == SWITCH){
        token = lexer.GetToken();
        if(token.token_type == LPAREN){
            tempI = parse_expression();
            // if tempI != INT then throw type error
            // else if tempI = -1 ==> parse_expresssion retunred an ID, then go and change using searchList the type of ID to 1.
            if(tempI!=0 && tempI<3){
                cout<<"TYPE MISMATCH "<<token.line_no<<" C5"<<endl;
                exit(1);
            }else if(tempI>2){
                update(tempI, 0);
            }
            token = lexer.GetToken();
            if(token.token_type == RPAREN){
                token = lexer.GetToken();
                if(token.token_type == LBRACE){
                    tempI = parse_caselist();
                    token = lexer.GetToken();
                    if(token.token_type == RBRACE){
                    }else{
                        exit(1);
                    }   
                }else{
                    exit(1);
                }
                
            }else{
                exit(1);
            }
        }else{
            exit(1);
        }    
    }else{
        exit(1);
    }
    return(0);
}


int Parser::parse_whilestmt(void){
    int tempI;
    token = lexer.GetToken();

    if(token.token_type == WHILE){
        token = lexer.GetToken();
        if(token.token_type == LPAREN){
            tempI = parse_expression();
            // if tempI != bool then throw type error
            // else if tempI = -1 ==> parse_expresssion retunred an ID, then go and change using searchList the type of ID to 2.
             if(tempI!=2 && tempI<3){
                cout<<"TYPE MISMATCH "<<token.line_no<<" C4"<<endl;
                exit(1);
            }else if(tempI>2){
                update(tempI, 2);
            }
            token = lexer.GetToken();
            if(token.token_type == RPAREN){
                tempI = parse_body();
            }else{
                exit(1);
            }
        }else{
            exit(1);
        }    
    }else{
        exit(1);
    }
    return(0);
}

int Parser::parse_ifstmt(void){
    int tempI;
    token = lexer.GetToken();

    if(token.token_type == IF){
        token = lexer.GetToken();
        if(token.token_type == LPAREN){
            tempI = parse_expression();
            // if tempI != bool then throw type error
            // else if tempI = -1 ==> parse_expresssion retunred an ID, then go and change using searchList the type of ID to 2.
             if(tempI!=2 && tempI<3){
                cout<<"TYPE MISMATCH "<<token.line_no<<" C4"<<endl;
                exit(1);
            }else if(tempI>2){
                update(tempI, 2);
            }
            token = lexer.GetToken();
            if(token.token_type == RPAREN){
                tempI = parse_body();
            }else{
                exit(1);
            }
        }else{
            exit(1);
        }    
    }else{
        exit(1);
    }
    return(0);
}

int Parser::parse_stmt(void){
    int tempI;
    token = lexer.GetToken();

    if(token.token_type == ID){
        tempTokenType = lexer.UngetToken(token);
        tempI = parse_assstmt();        
    }else if(token.token_type == IF){
        tempTokenType = lexer.UngetToken(token);
        tempI = parse_ifstmt();
    }else if(token.token_type == WHILE){
        tempTokenType = lexer.UngetToken(token);
        tempI = parse_whilestmt();
    }else if(token.token_type == SWITCH){
        tempTokenType = lexer.UngetToken(token);
        tempI = parse_switchstmt();
    }else{
        exit(1);
    }
    return(0);
}

int Parser::parse_stmtlist(void){
    token = lexer.GetToken();
    int tempI;

    if(token.token_type == ID || token.token_type == IF || token.token_type == WHILE || token.token_type == SWITCH){
        tempTokenType = lexer.UngetToken(token);
        tempI = parse_stmt();
        token = lexer.GetToken();
        if(token.token_type == ID || token.token_type == IF || token.token_type == WHILE || token.token_type == SWITCH){
            tempTokenType = lexer.UngetToken(token);
            tempI = parse_stmtlist();
        }else if (token.token_type == RBRACE){
            tempTokenType = lexer.UngetToken(token);
        }
    }else{
        exit(1);
    }
    return(0);
}



int Parser::parse_body(void){
    token = lexer.GetToken();
    int tempI;
    
        if(token.token_type == LBRACE){
            tempI = parse_stmtlist();
            token = lexer.GetToken();
            if(token.token_type == RBRACE){
                return(0);
            }else{
                exit(1);
            }    
        }else if(token.token_type == END_OF_FILE){
            tempTokenType = lexer.UngetToken(token);
        return(0);
        }else{
            exit(1);
        }
}




// parse scope end
int Parser::parse_typename(void){
    token = lexer.GetToken();
    if(token.token_type == INT) return 0;
    else if( token.token_type == REAL) return 1;
    else if(token.token_type == BOO) return 2;
    else exit(1);   
}

int Parser::parse_vardecl(void){
    int tempI;
    token = lexer.GetToken();

    if(token.token_type == ID){
        tempTokenType = lexer.UngetToken(token);
        tempI = parse_varlist();
        token = lexer.GetToken();
        if(token.token_type == COLON){
            tempI = parse_typename();
            
            token = lexer.GetToken();
            if(token.token_type == SEMICOLON){
                //use the searchList to update the types of variables that are already in the symbolTable
                for(int i=0;i<var_decl.size();i++) addList(var_decl[i], tempI);
                var_decl.clear();
                
            }else{
                exit(1);
            }
        } else{
            exit(1);
        } 
    }else{
        exit(1);
    }
    return(0);
}

int Parser::parse_vardecllist(void){
    int tempI;    
    token = lexer.GetToken();

    while(token.token_type == ID){
        tempTokenType = lexer.UngetToken(token);
        tempI = parse_vardecl();
        token = lexer.GetToken();
        if(token.token_type != ID){
        }else{
        }
    }
    tempTokenType = lexer.UngetToken(token);
    return(0);
}


string global = "::";
// parse global vars
int Parser::parse_globalVars(void){
    token = lexer.GetToken();
    int tempI;
    
    //check first set of var_list SEMICOLON
    if(token.token_type == ID){
        tempTokenType = lexer.UngetToken(token);
        tempI = parse_vardecllist();
    } else{
        exit(1);
    }
    return(0);
}


int Parser::parse_program(void){
    token = lexer.GetToken();
    int tempI;

    while (token.token_type != END_OF_FILE)
    {
        // Check first set of global_vars scope
            if(token.token_type == ID){
            tempTokenType = lexer.UngetToken(token);
            tempI = parse_globalVars();
            tempI = parse_body();
            }else if(token.token_type == LBRACE){
                tempTokenType = lexer.UngetToken(token);
                tempI = parse_body();
            }else if(token.token_type == END_OF_FILE){
                return(0);
            }else{
                exit(1);
                return(0);
            }
        token = lexer.GetToken();
    }
    return(0);
}

char null[] = "NULL";
int main()
{
    int i;
    Parser* parseProgram = new Parser();
    parseProgram->parse_program();
    printList();
    
}
