
use ESTOK; 

CREATE TABLE Usuarios (
    id int PRIMARY KEY AUTO_INCREMENT,
    nome varchar(255) NOT NULL,
    email varchar(255) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    perfil ENUM('Admin', 'Funcionario') NOT NULL
);

CREATE TABLE Tarefas (
	id int PRIMARY KEY auto_increment,
    tituto varchar(255) not null unique,
    descricao varchar(255),
    dataCadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	prazo DATE not null,
    statusTarefas ENUM('Pendante', 'Em_Andamento', 'Concluida') not null,
    id_usuario INT,
    
    constraint fk_usuario_tarefa
		foreign key (id_usuario)
        references Usuarios(id)
        on delete cascade
);

CREATE TABLE ItensTarefa (
	id INT PRIMARY KEY AUTO_INCREMENT,
	statusItemTarefa ENUM('Pendente', 'Conferido') not null,
    dataConferencia date not null,
    id_tarefa INT,
    
    constraint fk_tarefa_itemtarefa
    foreign key (id_tarefa)
    references Tarefas(id)
    on delete cascade
);

create table Itens (
	id int primary key auto_increment,
    id_itemTarefa int,
    id_localizacao int,
    codigoUnico varchar(255) not null unique,
    nome varchar(255) not null,
    descricao varchar(255),
	dataCadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    constraint fk_localizacao_item
    foreign key (id_localizacao)
    references Localizacoes(id)
    on delete cascade,
    
    constraint fk_itenstarefa_item
    foreign key (id_itemTarefa)
    references ItensTarefa(id)
    on delete cascade
);

create table Localizacoes (
	id int primary key auto_increment,
    nome varchar(255) not null,
	cep char(8) not null,
    logradouro VARCHAR(255) NOT NULL,
    numero VARCHAR(20) NOT NULL,
    complemento VARCHAR(100),
    bairro VARCHAR(100) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    estado CHAR(2) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    tipo_endereco ENUM('Residencial', 'Comercial', 'Entrega', 'Cobranca') DEFAULT 'Entrega',
    principal BOOLEAN DEFAULT FALSE,
    
	dataCadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

